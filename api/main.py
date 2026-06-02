import os
import json
import uuid
import time
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

load_dotenv()

app = FastAPI(title="Sistema Nutricional - API Productor")

class PlanRequest(BaseModel):
    paciente_id: int
    tipo_plan: str

def get_dynamodb_resource():
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
    return boto3.resource(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "mock"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "mock")
    )

def get_or_create_table():
    db = get_dynamodb_resource()
    table_name = "tasks"
    try:
        table = db.Table(table_name)
        table.load()  # triggers exception if table does not exist
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create the table
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'task_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'task_id',
                        'AttributeType': 'S'  # String
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj

def process_plan_task(task_id: str, paciente_id: int, tipo_plan: str):
    """
    Simulación del procesamiento asíncrono en segundo plano (RF10).
    """
    try:
        table = get_or_create_table()
        
        # Transición: PENDIENTE -> PROCESANDO
        print(f" [x] Iniciando tarea {task_id} en segundo plano para paciente {paciente_id}")
        table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET estado_actual = :state, started_at = :started, updated_at = :updated",
            ExpressionAttributeValues={
                ":state": "PROCESANDO",
                ":started": datetime.utcnow().isoformat(),
                ":updated": datetime.utcnow().isoformat()
            }
        )
        
        # Simulación del cálculo pesado
        time.sleep(5)
        
        # Transición: PROCESANDO -> COMPLETADO
        table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET estado_actual = :state, finished_at = :finished, updated_at = :updated",
            ExpressionAttributeValues={
                ":state": "COMPLETADO",
                ":finished": datetime.utcnow().isoformat(),
                ":updated": datetime.utcnow().isoformat()
            }
        )
        print(f" [v] Tarea {task_id} completada con éxito.")

    except Exception as e:
        print(f" [!] Error procesando tarea {task_id}: {e}")
        try:
            table = get_or_create_table()
            table.update_item(
                Key={"task_id": task_id},
                UpdateExpression="SET estado_actual = :state, error_message = :err, updated_at = :updated",
                ExpressionAttributeValues={
                    ":state": "FALLIDO",
                    ":err": str(e),
                    ":updated": datetime.utcnow().isoformat()
                }
            )
        except Exception as db_err:
            print(f"Error actualizando tarea a FALLIDO en base de datos: {db_err}")

@app.post("/plan", status_code=202) # Cambiado a 202
async def create_plan(plan: PlanRequest, background_tasks: BackgroundTasks):
    # LÓGICA RF10 
    
    # Generar task_id único 
    task_id = str(uuid.uuid4())
    
    # Preparar el registro para DynamoDB 
    task_data = {
        "task_id": task_id,
        "paciente_id": plan.paciente_id,
        "tipo_plan": plan.tipo_plan,
        "estado_actual": "PENDIENTE",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "attempt": 0
    }
    
    try:
        # Registrar en DynamoDB
        table = get_or_create_table()
        table.put_item(Item=task_data)

        # Agregar tarea a la cola de procesamiento en segundo plano de FastAPI
        background_tasks.add_task(process_plan_task, task_id, plan.paciente_id, plan.tipo_plan)
        
        return {
            "task_id": task_id, 
            "status": "PENDIENTE", 
            "message": "Solicitud recibida y registrada",
            "status_url": f"/tasks/{task_id}",
            "ready_url": f"/tasks/{task_id}/ready",
            "poll_interval_seconds": 2
        }

    except Exception as e:
        # Si algo falla, marcar como FALLIDO en la base de datos
        try:
            table = get_or_create_table()
            table.update_item(
                Key={"task_id": task_id},
                UpdateExpression="SET estado_actual = :state, error_message = :err, updated_at = :updated",
                ExpressionAttributeValues={
                    ":state": "FALLIDO",
                    ":err": str(e),
                    ":updated": datetime.utcnow().isoformat()
                }
            )
        except Exception as db_err:
            print(f"Error updating task to FAILED: {db_err}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ENDPOINTS DE CONSULTA 

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Permite consultar el estado actual de una tarea específica."""
    table = get_or_create_table()
    try:
        response = table.get_item(Key={"task_id": task_id})
        item = response.get("Item")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if not item:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")
    
    return convert_decimals(item)

@app.get("/tasks/{task_id}/ready")
async def get_task_ready(task_id: str):
    """
    Endpoint de consulta rápida para polling.
    ready=True únicamente cuando la tarea terminó con éxito.
    """
    table = get_or_create_table()
    try:
        response = table.get_item(Key={"task_id": task_id})
        task = response.get("Item")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not task:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")

    status = task.get("estado_actual", "DESCONOCIDO")
    ready = status == "COMPLETADO"
    terminal = status in {"COMPLETADO", "FALLIDO"}

    return {
        "task_id": task_id,
        "ready": ready,
        "status": status,
        "terminal": terminal,
        "should_continue_polling": not terminal,
        "poll_interval_seconds": 2,
        "updated_at": task.get("updated_at"),
        "finished_at": task.get("finished_at")
    }

@app.get("/")
async def health_check():
    return {"status": "online", "service": "api-nutricion"}


