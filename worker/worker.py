import os
import pika
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import firestore

# Conexión a la base de datos compartida 
db = firestore.Client()

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

def callback(ch, method, properties, body):
    """
    Función que procesa los mensajes y actualiza los estados en Firestore (RF10).
    """
    try:
        data = json.loads(body)
        # Leer task_id del mensaje
        task_id = data.get('task_id')
        paciente_id = data.get('paciente_id')
        
        if not task_id:
            print(" [!] Mensaje recibido sin task_id. No se puede trazar.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        task_ref = db.collection("tasks").document(task_id)

        # Transición: PENDIENTE -> PROCESANDO 
        print(f" [x] Iniciando tarea {task_id} para paciente {paciente_id}")
        task_ref.update({
            "estado_actual": "PROCESANDO",
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Simulación del cálculo pesado
        time.sleep(5) 
        
        # Transición: PROCESANDO -> COMPLETADO 
        task_ref.update({
            "estado_actual": "COMPLETADO",
            "finished_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        print(f" [v] Tarea {task_id} completada con éxito.")
        
        # Confirmar a RabbitMQ solo si la DB se actualizó 
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f" [!] Error procesando tarea: {e}")
        # Transición: PROCESANDO -> FALLIDO 
        if 'task_id' in locals():
            db.collection("tasks").document(task_id).update({
                "estado_actual": "FALLIDO",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            })
        
        # Confirmamos el fallo para que el mensaje no se quede infinito en la cola
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print(f" [*] Conectando a RabbitMQ en: {RABBITMQ_URL}")
    
    connection = None
    while not connection:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print(f" [!] Reintentando conexión...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue='cola_nutricion', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='cola_nutricion', on_message_callback=callback)

    print(' [*] Worker activo y trazando estados (RF10). CTRL+C para salir.')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' [*] Worker detenido.')