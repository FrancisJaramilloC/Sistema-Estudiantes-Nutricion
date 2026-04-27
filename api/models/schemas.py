from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlanRequest(BaseModel):
    """Modelo para solicitar la creación de un nuevo plan nutricional."""
    paciente_id: int
    tipo_plan: str

class TaskResponse(BaseModel):
    """Modelo para la respuesta de creación de plan."""
    task_id: str
    status: str
    message: str
    status_url: str
    ready_url: str
    poll_interval_seconds: int

class TaskStatusResponse(BaseModel):
    """Modelo para la respuesta de estado de tarea."""
    task_id: str
    paciente_id: int
    tipo_plan: str
    estado_actual: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    attempt: int

class TaskReadyResponse(BaseModel):
    """Modelo para la respuesta de consulta rápida (polling)."""
    task_id: str
    ready: bool
    status: str
    terminal: bool
    should_continue_polling: bool
    poll_interval_seconds: int
    updated_at: Optional[datetime]
    finished_at: Optional[datetime]
