import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import Response
from botocore.exceptions import ClientError
from app.models import PlanRequest
from app.database import get_or_create_table, convert_decimals
from app.auth import require_role
from app.tasks import process_plan_task
from app.pdf_generator import generar_pdf_plan

router = APIRouter()

@router.post("/plan", status_code=202)
async def create_plan(
    plan: PlanRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
    task_id = str(uuid.uuid4())
    task_data = {
        "task_id": task_id,
        "paciente_id": plan.paciente_id,
        "tipo_plan": plan.tipo_plan,
        "alimentos": [a.model_dump() for a in plan.alimentos] if plan.alimentos else [],
        "estado_actual": "PENDIENTE",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "attempt": 0
    }
    try:
        table = get_or_create_table()
        table.put_item(Item=task_data)
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
            print(f"Error al actualizar tarea a FALLIDO: {db_err}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
    table = get_or_create_table()
    try:
        response = table.get_item(Key={"task_id": task_id})
        item = response.get("Item")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not item:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")
    return convert_decimals(item)

@router.get("/tasks/{task_id}/ready")
async def get_task_ready(
    task_id: str,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
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

@router.get("/plan/{task_id}/pdf")
async def download_plan_pdf(
    task_id: str,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
    table = get_or_create_table()
    try:
        response = table.get_item(Key={"task_id": task_id})
        task = response.get("Item")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")

    task = convert_decimals(task)
    pdf_buf = generar_pdf_plan(task)
    filename = f"plan_nutricional_{task_id[:8]}.pdf"

    return Response(
        content=pdf_buf.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
