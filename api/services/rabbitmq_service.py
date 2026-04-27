import json
import pika
from config import RABBITMQ_URL, RABBITMQ_QUEUE


class RabbitMQService:
    """Servicio para operaciones de RabbitMQ."""
    
    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = RABBITMQ_QUEUE
    
    def publish_message(self, message: dict) -> None:
        """Publica un mensaje a la cola de RabbitMQ."""
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            
            # Declarar la cola como durable
            channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Publicar el mensaje
            channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                )
            )
            
            connection.close()
        
        except Exception as e:
            raise RuntimeError(f"Error al publicar mensaje en RabbitMQ: {str(e)}")
