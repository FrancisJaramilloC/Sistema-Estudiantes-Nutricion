import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from repositories.firestore_repository import FirestoreRepository
from services.rabbitmq_service import RabbitMQService
from config import TaskState


class TaskService:
    """Servicio de lógica de negocio para tareas."""
    
    def __init__(
        self,
        repository: FirestoreRepository,
        rabbitmq_service: RabbitMQService
    ):
        self.repository = repository
        self.rabbitmq = rabbitmq_service
    
    def create_plan(self, paciente_id: int, tipo_plan: str) -> Dict[str, Any]:
        """
        Crea un nuevo plan nutricional.
        
        Returns:
            Dict con task_id, status, urls para polling, etc.
        """
        # Generar ID único para la tarea
        task_id = str(uuid.uuid4())
        
        # Preparar datos de la tarea
        task_data = {
            "task_id": task_id,
            "paciente_id": paciente_id,
            "tipo_plan": tipo_plan,
            "estado_actual": TaskState.PENDIENTE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "attempt": 0
        }
        
        try:
            # TEMPORALMENTE DESHABILITADO: Registrar en Firestore antes de publicar
            # self.repository.create_task(task_id, task_data)
            
            # Preparar mensaje para la cola
            message = {
                "task_id": task_id,
                "paciente_id": paciente_id,
                "tipo_plan": tipo_plan
            }
            
            # Publicar en RabbitMQ
            self.rabbitmq.publish_message(message)
            
            return {
                "task_id": task_id,
                "status": TaskState.PENDIENTE,
                "message": "Solicitud recibida y registrada",
                "status_url": f"/tasks/{task_id}",
                "ready_url": f"/tasks/{task_id}/ready",
                "poll_interval_seconds": 2
            }
        
        except Exception as e:
            # TEMPORALMENTE DESHABILITADO: Marcar como fallido si algo falla
            # self.repository.mark_task_failed(task_id, str(e))
            raise
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado completo de una tarea."""
        # TEMPORALMENTE DESHABILITADO: return self.repository.get_task(task_id)
        return {"task_id": task_id, "status": TaskState.PENDIENTE, "message": "Mock data - Firestore disabled"}
    
    def get_task_ready_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado para polling rápido.
        ready=True únicamente cuando la tarea está COMPLETADA.
        """
        # TEMPORALMENTE DESHABILITADO: task = self.repository.get_task(task_id)
        task = {"task_id": task_id, "estado_actual": TaskState.PENDIENTE}  # Mock data
        
        if not task:
            raise ValueError(f"Tarea {task_id} no encontrada")
        
        status = task.get("estado_actual", "DESCONOCIDO")
        ready = status == TaskState.COMPLETADO
        terminal = status in {TaskState.COMPLETADO, TaskState.FALLIDO}
        
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
