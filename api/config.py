import os
from dotenv import load_dotenv

load_dotenv()

# RabbitMQ Configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_QUEUE = "cola_nutricion"

# Task States
class TaskState:
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"

# Database Configuration
FIRESTORE_COLLECTION = "tasks"

# API Configuration
API_TITLE = "Sistema Nutricional - API Productor"
API_VERSION = "1.0.0"

# Polling Configuration
POLL_INTERVAL_SECONDS = 2
