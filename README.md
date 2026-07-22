# NutriA - Sistema de Gestion Nutricional (FastAPI + DynamoDB + React)

Plataforma integral para nutricionistas y estudiantes de nutricion. Incluye catalogo de alimentos, planificacion de dietas, sugerencias automaticas, calculo antropometrico, recuperacion de contrasena por correo, generacion de PDFs y auditoria completa.

## Arquitectura

```
Frontend (React + Vite) :3000 --> API (FastAPI) :8000 --> DynamoDB Local :8001
                                                      --> AWS Cognito (produccion)
                                                      --> Gmail SMTP (recuperacion de contrasena)
                                                      --> Grafana Cloud (monitoring)
```

### Servicios Docker

| Servicio | Puerto | Descripcion |
|---|---|---|
| `frontend` | 3000 | React SPA, hash-based routing |
| `api` | 8000 | FastAPI, JWT auth, RBAC |
| `dynamodb` | 8001 | DynamoDB Local (in-memory) |
| `alloy` | - | Grafana Alloy (telemetry) |

## Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Instalacion

```bash
git clone https://github.com/FrancisJaramilloC/Sistema-Estudiantes-Nutricion.git
cd Sistema-Estudiantes-Nutricion
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **API docs:** http://localhost:8000/docs
- **DynamoDB:** http://localhost:8001

### Auto-seed

Al iniciar, el sistema crea automaticamente:
- **24 usuarios** (4 docentes, 20 estudiantes) con contrasena `Password123*`
- **949 alimentos** extraidos de la tabla de composicion nutricional USFQ

## Funcionalidades

### 1. Autenticacion y Roles (RBAC)

| Rol | Permisos |
|---|---|
| **Estudiantes** | Ver inicio, antropometria, plan alimenticio, ritmo cardiaco |
| **Docentes** | Todo lo anterior + gestion de usuarios, auditoria, administracion |

- Login con JWT (24h de expiracion)
- Registro con validacion de cedula ecuatoriana, mayoridad (18+), y politica de contrasena (8+ caracteres, mayuscula, minuscula, numero, simbolo)
- Recuperacion de contrasena via correo SMTP (Gmail)
- Auto-bloqueo por intentos fallidos

### 2. Catalogo de Alimentos (949 alimentos)

- Busqueda por nombre y categoria (15 categorias)
- Detalle completo por 100g: 14 macro/micronutrientes
- Endpoints: `GET /api/v1/alimentos`, `GET /api/v1/alimentos/{id}`, `GET /api/v1/alimentos/categorias`

### 3. Planificacion de Dietas

- Constructor visual de planes alimenticios
- Agregar/quitar alimentos desde el catalogo con ajuste de gramos
- Asignar a comidas: Desayuno, Almuerzo, Cena, Colacion
- Calculo automatico de nutrientes en tiempo real
- Resumen nutricional con barras de color dinamicas (verde/amarillo/rojo)
- Alertas nutricionales automaticas (exceso calorico, sodio, fibra, grasa saturada)
- Guardar plan en DynamoDB con recálculo server-side
- Descarga de PDF completo con logo Nutria

### 4. PDF Nutricional

- Logo Nutria + header profesional
- Datos del plan (paciente, tipo, estado, creador, fecha)
- Distribucion de macronutrientes (gramos + porcentaje)
- Tabla de totales diarios (13 nutrientes)
- Desglose por comida con subtotales
- Endpoint: `GET /api/v1/planes/{plan_id}/pdf`

### 5. Sugerencias de Planes

- Generacion automatica basada en parametros del paciente (peso, estatura, edad, sexo, actividad, objetivo)
- Calculo de TMB (Harris-Benedict) y GET
- Distribucion de macros recomendada
- Selección de alimentos del catalogo por categoria
- Aceptar sugerencia → crea plan alimenticio completo
- Historial de sugerencias por paciente

### 6. Motor Antropometrico

- IMC con clasificacion OMS
- ICC con riesgo cardiovascular
- Distribucion de grasa corporal (androide/ginoide)
- TMB y GET

### 7. Ritmo Cardiaco (ESP32)

- Registro de dispositivos ESP32
- Lecturas de frecuencia cardiaca en tiempo real
- Dashboard con graficas y alertas

### 8. Auditoria Completa (RNF9)

- Login/Logout exitosos y fallidos
- Crear/Eliminar usuarios
- Cambio de roles
- Solicitud/Restablecimiento de contrasena
- Crear/Eliminar planes
- Descarga de PDFs
- Panel de auditoria con filtros por tipo, usuario y fecha

### 9. Monitoreo

- Metricas Prometheus en `/metrics`
- Grafana Alloy para telemetria
- Logs estructurados

## Endpoints Principales

### Auth
- `POST /api/v1/auth/register` - Registro (fuerza rol Estudiantes)
- `POST /api/v1/auth/login` - Login, retorna JWT
- `POST /api/v1/auth/logout` - Cierre de sesion
- `POST /api/v1/auth/forgot-password` - Solicitud de recuperacion (envia correo)
- `POST /api/v1/auth/reset-password` - Restablecer contrasena

### Alimentos
- `GET /api/v1/alimentos` - Buscar alimentos (busqueda, categoria, paginacion)
- `GET /api/v1/alimentos/categorias` - Lista de categorias
- `GET /api/v1/alimentos/{id}` - Detalle de alimento

### Planes
- `POST /api/v1/planes` - Crear plan alimenticio
- `GET /api/v1/planes/{plan_id}` - Obtener plan
- `GET /api/v1/planes/{plan_id}/pdf` - Descargar PDF
- `PUT /api/v1/planes/{plan_id}` - Actualizar plan
- `DELETE /api/v1/planes/{plan_id}` - Eliminar plan

### Sugerencias
- `POST /api/v1/sugerencia/generar` - Generar sugerencia
- `POST /api/v1/sugerencia/{id}/aceptar` - Aceptar y crear plan
- `GET /api/v1/sugerencia/historial/{paciente_id}` - Historial

### Admin (solo Docentes)
- `GET /api/v1/admin/users` - Listar usuarios
- `POST /api/v1/admin/create-user` - Crear usuario con cualquier rol
- `DELETE /api/v1/admin/users/{username}` - Eliminar usuario
- `PUT /api/v1/admin/users/{username}/role` - Cambiar rol
- `GET /api/v1/admin/audit/all` - Panel de auditoria (filtros)

### Clinico
- `POST /api/v1/clinical/calculate` - Calculo antropometrico

## Credenciales de Prueba

| Usuario | Contrasena | Rol |
|---|---|---|
| `docente_patricia` | `Password123*` | Docentes |
| `docente_luisa` | `Password123*` | Docentes |
| `docente_ricardo` | `Password123*` | Docentes |
| `docente_hugo` | `Password123*` | Docentes |
| `ana` | `Password123*` | Estudiantes |
| `carlos` | `Password123*` | Estudiantes |

## Variables de Entorno (.env)

```env
# AWS
AWS_ACCESS_KEY_ID=mock
AWS_SECRET_ACCESS_KEY=mock
AWS_DEFAULT_REGION=us-east-2

# Cognito (mock = auth local, real = AWS Cognito)
COGNITO_USER_POOL_ID=mock
COGNITO_APP_CLIENT_ID=mock

# DynamoDB (vacio en AWS = DynamoDB real)
DYNAMODB_ENDPOINT_URL=http://dynamodb:8000

# JWT
JWT_SECRET=nutria-secret-key-12345

# SMTP (recuperacion de contrasena)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=system.nutria@gmail.com
SMTP_PASS=akyy dppe mmdf dgah
SMTP_FROM=NutriA <system.nutria@gmail.com>

# Grafana Cloud
GRAFANA_CLOUD_PROMETHEUS_URL=...
GRAFANA_CLOUD_PROMETHEUS_USER=...
GRAFANA_CLOUD_PROMETHEUS_API_KEY=...
```

## Estructura del Proyecto

```
Sistema-Estudiantes-Nutricion/
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # Startup, CORS, auto-seed
│   │   ├── config.py                # Variables de entorno
│   │   ├── auth.py                  # JWT middleware, RBAC
│   │   ├── database.py              # DynamoDB tables + seed
│   │   ├── models.py                # Pydantic models
│   │   ├── audit.py                 # Logging de auditoria
│   │   ├── monitoring.py            # Prometheus metrics
│   │   ├── pdf_generator.py         # Generacion PDF con fpdf2
│   │   ├── nutria-logo.png          # Logo para PDFs
│   │   ├── alimentos_usfq.json      # 949 alimentos (para seed)
│   │   ├── routes/
│   │   │   ├── auth.py              # Login, registro, recuperacion
│   │   │   ├── alimentos.py         # Catalogo de alimentos
│   │   │   ├── plan_nutricional.py  # CRUD planes + PDF
│   │   │   ├── sugerencia.py        # Generacion de sugerencias
│   │   │   ├── admin.py             # Gestion usuarios + auditoria
│   │   │   ├── clinical.py          # Calculo antropometrico
│   │   │   ├── health.py            # Health check
│   │   │   ├── plans.py             # Endpoints legacy
│   │   │   └── devices.py           # Dispositivos ESP32
│   │   └── services/
│   │       └── email_service.py     # Envio SMTP
│   └── tests/                       # 177 tests
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.jsx                  # Router principal
│       ├── index.css                # Estilos (Forest Green + Crema)
│       ├── services/api.js          # Cliente HTTP
│       └── components/
│           ├── LoginRegister.jsx    # Login + Registro + Recuperacion
│           ├── Dashboard.jsx        # Panel principal
│           ├── Sidebar.jsx          # Navegacion
│           ├── PlanAlimenticio.jsx  # Constructor de planes + catalogo
│           ├── AntropometriaDashboard.jsx  # Antropometria + sugerencias
│           ├── AlertasNutricionales.jsx    # Alertas automaticas
│           ├── AuditoriaPanel.jsx   # Panel de auditoria
│           ├── HeartRateDashboard.jsx      # Ritmo cardiaco
│           └── AccessibilityButton.jsx     # Controles de accesibilidad
├── scripts/
│   ├── extract_alimentos.py         # Extraccion PDF → JSON
│   ├── reclassify_alimentos.py      # Clasificacion por categorias
│   ├── seed_alimentos.py            # Seed a DynamoDB
│   └── alimentos_usfq.json          # Datos extraidos
└── RitmoCardiacoESP32/              # Firmware ESP32
```

## Despliegue en AWS

1. Crear tabla DynamoDB real (on-demand)
2. Crear User Pool en Cognito con grupo "Estudiantes" y "Docentes"
3. Actualizar `.env`:
   - `DYNAMODB_ENDPOINT_URL=` (vacio)
   - `COGNITO_USER_POOL_ID=tu_pool_id`
   - `COGNITO_APP_CLIENT_ID=tu_client_id`
4. Ejecutar `docker compose up --build`
5. El auto-seed crea usuarios y alimentos en la primera ejecucion
