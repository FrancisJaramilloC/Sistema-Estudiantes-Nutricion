from functools import lru_cache
from google.cloud import firestore

from services.task_service import TaskService
from services.rabbitmq_service import RabbitMQService
from repositories.firestore_repository import FirestoreRepository


@lru_cache(maxsize=1)
def get_firestore_client() -> firestore.Client:
    """Obtiene una instancia única del cliente de Firestore."""
    # TEMPORALMENTE DESHABILITADO: return firestore.Client()
    return None  # Mock - Firestore disabled


@lru_cache(maxsize=1)
def get_firestore_repository() -> FirestoreRepository:
    """Obtiene una instancia única del repositorio de Firestore."""
    # TEMPORALMENTE DESHABILITADO: client = get_firestore_client()
    # return FirestoreRepository(client)
    return None  # Mock - Firestore disabled


@lru_cache(maxsize=1)
def get_rabbitmq_service() -> RabbitMQService:
    """Obtiene una instancia única del servicio de RabbitMQ."""
    return RabbitMQService()


@lru_cache(maxsize=1)
def get_task_service() -> TaskService:
    """Obtiene una instancia única del servicio de tareas."""
    repository = get_firestore_repository()
    rabbitmq = get_rabbitmq_service()
    return TaskService(repository, rabbitmq)
