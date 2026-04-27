from google.cloud import firestore
from datetime import datetime
from typing import Dict, Any, Optional
from config import FIRESTORE_COLLECTION, TaskState


class FirestoreRepository:
    """Repositorio para operaciones de Firestore."""
    
    def __init__(self, client: firestore.Client):
        self.db = client
        self.collection_name = FIRESTORE_COLLECTION
    
    def create_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Crea una nueva tarea en Firestore."""
        self.db.collection(self.collection_name).document(task_id).set(task_data)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una tarea por su ID."""
        doc = self.db.collection(self.collection_name).document(task_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> None:
        """Actualiza una tarea existente."""
        self.db.collection(self.collection_name).document(task_id).update(update_data)
    
    def update_task_state(
        self,
        task_id: str,
        new_state: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Actualiza el estado de una tarea."""
        update_data = {
            "estado_actual": new_state,
            "updated_at": datetime.utcnow()
        }
        
        if additional_data:
            update_data.update(additional_data)
        
        self.update_task(task_id, update_data)
    
    def mark_task_failed(self, task_id: str, error_message: str) -> None:
        """Marca una tarea como fallida."""
        self.update_task_state(
            task_id,
            TaskState.FALLIDO,
            {"error_message": error_message}
        )
