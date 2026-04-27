import os
import json
import pika
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google.cloud import firestore

# Configuración de la base de datos compartida 
db = firestore.Client()

load_dotenv()

app = FastAPI(title="Sistema Nutricional - API Productor")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

class PlanRequest(BaseModel):
    paciente_id: int
    tipo_plan: str

def get_rabbitmq_connection():
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)

@app.post("/plan", status_code=202) # Cambiado a 202
async def create_plan(plan: PlanRequest):
    # LÓGICA RF10 
    
    # Generar task_id único 
    task_id = str(uuid.uuid4())
    
    # Preparar el registro para Firestore 
    task_data = {
        "task_id": task_id,
        "paciente_id": plan.paciente_id,
        "tipo_plan": plan.tipo_plan,
        "estado_actual": "PENDIENTE",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "attempt": 0
    }
    
    try:
        # Registrar en Firestore antes del publish
        db.collection("tasks").document(task_id).set(task_data)

        # Publicar mensaje incluyendo el task_id 
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='cola_nutricion', durable=True)
        
        # El mensaje ahora incluye el task_id para que el Worker sepa a quién actualizar
        message = plan.dict()
        message["task_id"] = task_id 
        
        channel.basic_publish(
            exchange='',
            routing_key='cola_nutricion',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))
        
        connection.close()
        
        return {
            "task_id": task_id, 
            "status": "PENDIENTE", 
            "message": "Solicitud recibida y registrada"
        }

    except Exception as e:
        # Si algo falla, marcar como FALLIDO en la base de datos
        db.collection("tasks").document(task_id).update({
            "estado_actual": "FALLIDO",
            "error_message": str(e),
            "updated_at": datetime.utcnow()
        })
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# NUEVOS ENDPOINTS DE CONSULTA 

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Permite consultar el estado actual de una tarea específica."""
    task_ref = db.collection("tasks").document(task_id).get()
    
    if not task_ref.exists:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")
        
    return task_ref.to_dict()

@app.get("/")
async def health_check():
    return {"status": "online", "service": "api-nutricion"}