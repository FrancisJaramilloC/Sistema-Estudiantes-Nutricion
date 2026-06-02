# Informe de Despliegue Técnico y Justificación de Arquitectura en AWS (TFA)

Este documento sirve como el **Informe Técnico de Puesta en Marcha** y la **Guía de Despliegue** para el Trabajo Final de Asignatura (TFA) del **Sistema Nutricional Asíncrono**. Se detalla la justificación de cada componente utilizado en la nube de AWS (orientado a cuentas de AWS Academy / Estudiante) y el paso a paso para conectar la aplicación a los servicios reales de AWS.

---

## 1. Justificación Técnica de la Arquitectura en la Nube (AWS)

La arquitectura propuesta está diseñada para ser resiliente, costo-eficiente y altamente escalable, aprovechando los siguientes pilares de cómputo en la nube de Amazon Web Services (AWS):

### A. Procesamiento (Cómputo)
*   **AWS EC2 (Elastic Compute Cloud) / AWS ECS (Elastic Container Service) con Fargate:**
    *   *Justificación:* Para la ejecución de la API construida en **FastAPI**, se seleccionó un enfoque de contenedores. Para despliegues educativos en AWS Academy, se propone una instancia **t2.micro** o **t3.micro** (elegible en la capa gratuita) configurada con Docker. En entornos de producción, el uso de **AWS ECS con Fargate (Serverless)** elimina la sobrecarga operativa de gestionar sistemas operativos y parches de seguridad, cobrando únicamente por el tiempo exacto de CPU y memoria consumido por el contenedor FastAPI.
    *   *Virtualización y OS:* El microservicio se ejecuta en un contenedor Docker basado en **Debian Slim / Python 3.11**, optimizando el espacio en disco, reduciendo la superficie de ataque de seguridad y garantizando que la aplicación sea portable entre el entorno de desarrollo local y la nube de AWS.

### B. Almacenamiento (Base de Datos NoSQL)
*   **AWS DynamoDB:**
    *   *Justificación:* Para almacenar el estado y la trazabilidad de las solicitudes de planes nutricionales (`PENDIENTE`, `PROCESANDO`, `COMPLETADO`, `FALLIDO`), se utiliza **AWS DynamoDB**.
    *   *Ventajas clave:*
        *   **Serverless:** No requiere provisionar servidores ni administrar clústeres de base de datos.
        *   **Rendimiento:** Latencia de un solo dígito de milisegundo a cualquier escala.
        *   **Modelo de Datos Clave-Valor:** Al estructurarse en torno a un `task_id` (UUID), DynamoDB permite realizar consultas directas (`GetItem`) extremadamente rápidas y eficientes por clave primaria, reduciendo costos de lectura y escritura.
        *   **Capa Gratuita:** DynamoDB ofrece hasta 25 GB de almacenamiento y 25 WCU / 25 RCU de forma totalmente gratuita, lo cual es ideal para presupuestos estudiantiles.

### C. Redes y Seguridad (Networking)
*   **VPC (Virtual Private Cloud) y Security Groups:**
    *   *Justificación:* El contenedor de la API se despliega dentro de una subred pública para recibir tráfico HTTP del cliente. El tráfico está controlado por **Security Groups** que actúan como firewalls virtuales de estado, permitiendo únicamente conexiones entrantes por el puerto `80` (HTTP) y `443` (HTTPS) desde internet.
    *   *Seguridad de Datos:* A diferencia de las bases de datos SQL tradicionales que requieren abrir puertos de red (como el 3306 de MySQL o 5432 de PostgreSQL), DynamoDB se expone a través de endpoints seguros HTTPS controlados mediante políticas de acceso de AWS **IAM (Identity and Access Management)**, eliminando la necesidad de exponer la base de datos a internet.

### D. DevOps e Infraestructura como Código (IaC)
*   **Contenedores y Pipeline:**
    *   *Justificación:* Todo el entorno local se configura mediante **Docker Compose**, lo que permite recrear el ambiente de nube localmente. Para producción, la integración de GitHub Actions permite empaquetar la imagen Docker y subirla a **AWS ECR (Elastic Container Registry)** para su posterior despliegue automatizado.

---

## 2. Paso a Paso para Configurar AWS DynamoDB en la Consola de AWS

Dado que cuentas con una cuenta estudiantil de AWS, sigue estos pasos para configurar la base de datos real en la nube:

1.  **Iniciar sesión en la consola de AWS:**
    *   Entra a tu portal de AWS Academy (o consola estudiantil) y haz clic en **AWS Console**.
2.  **Ir al servicio DynamoDB:**
    *   En la barra de búsqueda superior, escribe **DynamoDB** y selecciona el servicio.
3.  **Crear la Tabla:**
    *   Haz clic en el botón **Crear tabla** (Create table).
    *   **Nombre de la tabla:** Escribe exactamente `tasks`.
    *   **Clave de partición (Partition Key):** Escribe exactamente `task_id` y selecciona el tipo **Cadena** (String / S).
    *   **Clave de ordenación (Sort Key):** Déjalo en blanco.
4.  **Configuración de la Tabla:**
    *   Selecciona **Configuración personalizada** (Custom settings).
    *   **Clase de tabla:** Selecciona *DynamoDB Estándar* (Standard).
    *   **Calculadora de capacidad:** Selecciona **Personalizado** (Customize).
    *   **Capacidad de lectura/escritura (Read/Write capacity):**
        *   Selecciona **Bajo demanda** (On-Demand / Pay-per-request). Esto evitará costos fijos cuando la aplicación no reciba solicitudes, cobrando únicamente fracciones de centavo por petición de lectura o escritura.
5.  **Crear:**
    *   Desplázate al final de la página y haz clic en **Crear tabla**. En unos segundos la tabla estará activa (`ACTIVE`) y lista en la nube de AWS.

---

## 3. Cómo Conectar tu Código a la Cuenta Real de AWS

Nuestra API de FastAPI ya está preparada de manera inteligente: **si detecta que las variables de entorno de AWS real están configuradas, se conectará automáticamente a la nube en lugar de la base de datos local.**

Existen dos métodos de conexión dependiendo de dónde ejecutes la aplicación:

### Método A: Ejecución Local apuntando a AWS Real (Ideal para Pruebas Rápidas)

Si quieres correr el Docker en tu computadora local pero que guarde la información en tu base de datos de AWS real:

1.  **Obtener las Credenciales de tu AWS Academy:**
    *   En tu portal de AWS Academy, haz clic en **AWS Details**.
    *   Verás una sección llamada **AWS CLI Credentials**. Copia los valores de:
        *   `aws_access_key_id`
        *   `aws_secret_access_key`
        *   `aws_session_token` (las cuentas estudiantiles usan tokens temporales obligatoriamente).
2.  **Configurar las Variables de Entorno en el archivo `.env`:**
    *   Crea un archivo llamado `.env` en la raíz de tu proyecto (este archivo está excluido en el `.gitignore` por seguridad).
    *   Añade las credenciales de tu consola estudiantil:
        ```env
        AWS_DEFAULT_REGION=us-east-1
        AWS_ACCESS_KEY_ID=TU_AWS_ACCESS_KEY_ID_REAL
        AWS_SECRET_ACCESS_KEY=TU_AWS_SECRET_ACCESS_KEY_REAL
        AWS_SESSION_TOKEN=TU_AWS_SESSION_TOKEN_COMPLETO
        ```
    *   *Nota Importante:* **NO** definas la variable `DYNAMODB_ENDPOINT_URL` en este archivo `.env`. Al no estar definida, la librería `boto3` sabrá que debe buscar la tabla `tasks` directamente en los servidores de AWS en internet, usando tus credenciales.

3.  **Ejecutar localmente:**
    *   Levanta tu contenedor:
        ```bash
        sudo docker compose up --build
        ```
    *   Haz una petición POST a tu API local. Verás en tu consola de AWS DynamoDB (sección *Explorar elementos de tabla*) cómo se registra la tarea directamente en la nube.

---

### Método B: Ejecución Desplegada en AWS (EC2 / ECS Fargate - Producción)

Cuando subas tu contenedor API a una máquina virtual **EC2** o servicio de contenedores **ECS Fargate** en AWS:

1.  **Seguridad por Roles (Sin contraseñas escritas):**
    *   **NUNCA** debes escribir o guardar archivos con claves de acceso (`AWS_ACCESS_KEY_ID`) en servidores en la nube.
    *   En su lugar, crea un **Rol de IAM** (IAM Role) con permisos para leer y escribir en DynamoDB (política `AmazonDynamoDBFullAccess` o una política personalizada restringida a la tabla `tasks`).
2.  **Asociar el Rol al Servidor:**
    *   Asocia este Rol de IAM al perfil de instancia de tu servidor EC2 o a la definición de tarea (Task Definition) en ECS Fargate.
3.  **El código funciona automáticamente:**
    *   Gracias al cambio estructural implementado en `get_dynamodb_resource()`, la librería `boto3` de Python detectará de manera automática el rol de la máquina de AWS y se autenticará de forma segura sin necesidad de configurar ninguna variable de credenciales en tu `.env` ni en el `docker-compose.yml`.
