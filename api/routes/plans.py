from fastapi import APIRouter, HTTPException, Depends

from models.schemas import PlanRequest, TaskResponse
from services.task_service import TaskService
from dependencies import get_task_service

router = APIRouter(prefix="/plan", tags=["plans"])


@router.post("", status_code=202, response_model=TaskResponse)
async def create_plan(
    plan: PlanRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Crea un nuevo plan nutricional.
    
    - **paciente_id**: ID del paciente (entero)
    - **tipo_plan**: Tipo de plan nutricional (string)
    
    Retorna un task_id para hacer polling del estado.
    """
    try:
        result = task_service.create_plan(plan.paciente_id, plan.tipo_plan)
        return TaskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
