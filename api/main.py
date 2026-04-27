import os
import json
import pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables de entorno (útil para desarrollo local fuera de Docker)
load_dotenv()

app = FastAPI(title="Sistema Nutricional - API Productor")

# URL de RabbitMQ obtenida de variables de entorno siguiendo 12-factor apps
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

class PlanRequest(BaseModel):
    paciente_id: int
    tipo_plan: str

def get_rabbitmq_connection():
    """Establece una conexión con el servidor de mensajería RabbitMQ."""
    params = pika.URLParameters(RABBITMQ_URL)
    return pika.BlockingConnection(params)

@app.post("/plan")
async def create_plan(plan: PlanRequest):
    """
    Endpoint para recibir una solicitud de plan nutricional y enviarla a la cola.
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Asegurar que la cola exista (durable=True para persistencia)
        channel.queue_declare(queue='cola_nutricion', durable=True)
        
        message = plan.dict()
        channel.basic_publish(
            exchange='',
            routing_key='cola_nutricion',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer que el mensaje sea persistente
            ))
        
        connection.close()
        return {"status": "Plan encolado con éxito", "mensaje": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando con RabbitMQ: {str(e)}")

@app.get("/")
async def health_check():
    return {"status": "online", "service": "api-nutricion"}
