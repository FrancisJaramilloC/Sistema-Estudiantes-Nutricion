from fastapi import APIRouter, HTTPException, Depends

from models.schemas import TaskStatusResponse, TaskReadyResponse
from services.task_service import TaskService
from dependencies import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Obtiene el estado completo de una tarea específica.
    
    Incluye: estado actual, timestamps, error_message si aplica, etc.
    """
    task = task_service.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")
    
    return TaskStatusResponse(**task)


@router.get("/{task_id}/ready", response_model=TaskReadyResponse)
async def get_task_ready(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Endpoint de consulta rápida para polling.
    
    ready=True únicamente cuando la tarea terminó con éxito (COMPLETADO).
    terminal=True cuando la tarea llegó a un estado final (COMPLETADO o FALLIDO).
    """
    try:
        result = task_service.get_task_ready_status(task_id)
        return TaskReadyResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="No se encontró la tarea")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
