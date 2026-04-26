import os
import pika
import time
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# URL de RabbitMQ desde el entorno para portabilidad (12-factor apps)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

def callback(ch, method, properties, body):
    """
    Función que procesa los mensajes recibidos de la cola.
    """
    try:
        data = json.loads(body)
        print(f" [x] Mensaje recibido del paciente ID: {data.get('paciente_id')}")
        print(f" [x] Tipo de plan solicitado: {data.get('tipo_plan')}")
        
        # Simulación de un cálculo nutricional complejo (e.g. generación de dieta con IA/Algoritmos)
        print(" [x] Iniciando cálculo pesado técnico...")
        time.sleep(5) 
        
        print(f" [v] Cálculo completado para el paciente {data.get('paciente_id')}.")
        
        # Confirmar procesamiento exitoso (Acknowledge)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f" [!] Error procesando mensaje: {e}")

def main():
    print(f" [*] Intentando conectar a la infraestructura de mensajería en: {RABBITMQ_URL}")
    
    # Lógica de reintento robusta para entornos distribuidos
    connection = None
    retry_count = 0
    while not connection:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            print(f" [!] Reintentando conexión con RabbitMQ ({retry_count})...")
            time.sleep(5)

    channel = connection.channel()
    
    # Asegurar que la cola existe
    channel.queue_declare(queue='cola_nutricion', durable=True)
    
    # Distribución equitativa de carga entre workers
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue='cola_nutricion', on_message_callback=callback)

    print(' [*] Consumidor activo. Esperando planes nutricionales. Para salir: CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' [*] Worker detenido manualmente.')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
