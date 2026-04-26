# Sistema Nutricional Distribuido (Productor-Consumidor)

Este proyecto es un boilerplate para un sistema de procesamiento nutricional basado en una arquitectura de microservicios distribuida, utilizando **RabbitMQ** como broker de mensajería, **FastAPI** para la API del productor y un **Worker** en Python para el procesamiento asíncrono.

## 🏗️ Arquitectura

El sistema consta de tres componentes principales orquestados con Docker:

1.  **API (Productor):** Recibe solicitudes de planes nutricionales a través de un endpoint REST y las encola en RabbitMQ.
2.  **RabbitMQ:** Gestiona la cola de mensajes `cola_nutricion`, garantizando que ninguna solicitud se pierda.
3.  **Worker (Consumidor):** Escucha la cola de mensajes y procesa cada plan de forma asíncrona (simulando cálculos pesados).

## 🚀 Requisitos

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

## 🛠️ Instalación y Despliegue

Para levantar todos los servicios, simplemente ejecuta:

```bash
docker compose up --build
```

Esto levantará:
*   **API:** [http://localhost:8000](http://localhost:8000)
*   **RabbitMQ Management (Panel):** [http://localhost:15672](http://localhost:15672) (Usuario: `guest`, Clave: `guest`)

## 🧪 Pruebas de la API

Puedes enviar una solicitud de plan nutricional usando `curl` o cualquier cliente REST (como Postman/Insomnia):

```bash
curl -X POST http://localhost:8000/plan \
     -H "Content-Type: application/json" \
     -d '{"paciente_id": 123, "tipo_plan": "Keto"}'
```

Al enviar esta petición:
1.  La **API** responderá con un mensaje de éxito.
2.  El **Worker** mostrará en los logs: `[x] Mensaje recibido del paciente ID: 123` e iniciará el procesamiento.
3.  Después de 5 segundos, el Worker confirmará que el cálculo ha finalizado.

## 📁 Estructura del Proyecto

```text
.
├── api/
│   ├── Dockerfile
│   └── main.py          # Lógica del productor (FastAPI)
├── worker/
│   ├── Dockerfile
│   └── worker.py        # Lógica del consumidor (Python puro)
├── docker-compose.yml   # Orquestación de contenedores
├── requirements.txt     # Dependencias de Python
└── .env                 # Variables de entorno (RABBITMQ_URL)
```

## 🔐 Configuración (12-Factor Apps)

La conexión a la infraestructura se gestiona mediante la variable de entorno `RABBITMQ_URL` definida en el archivo `docker-compose.yml` y replicada opcionalmente en el archivo `.env`.

---
Desarrollado para la gestión eficiente de planes nutricionales distribuidos.
