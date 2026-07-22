# MÓDULO DE MONITOREO FUNCIONAL SÍNCRONO

## Documentación de Análisis, Diseño e Implementación

> **Proyecto:** NUTRIA — Sistema de Gestión de Estudiantes de Nutrición
> **Backend:** FastAPI (Python 3.11) · **Base de datos:** DynamoDB Local (NoSQL)
> **Estándar de calidad:** ISO 25000 — Eficiencia, Seguridad y Privacidad

---

## ÍNDICE

1. [Alcance Técnico Funcional](#1-alcance-técnico-funcional)
2. [Especificación de Requisitos del Sistema](#2-especificación-de-requisitos-del-sistema)
   - 2.1 [Requisitos Funcionales (RF21–RF23)](#21-requisitos-funcionales-añadidos)
   - 2.2 [Requisitos No Funcionales (RNF1, RNF9)](#22-requisitos-no-funcionales-relacionados-métricas-iso-25000)
3. [Historias de Usuario](#3-historias-de-usuario)
   - 3.1 [HU-MON-01: Interceptor de Telemetría, Seguridad y Gobernanza de Datos](#31-hu-mon-01-interceptor-de-telemetría-seguridad-y-gobernanza-de-datos)
   - 3.2 [Criterios de Aceptación y Escenarios de Prueba](#32-criterios-de-aceptación-escenarios-de-pruebas)
4. [Diseño del Caso de Uso ICONIX](#4-diseño-del-caso-de-uso-iconix)
   - 4.1 [CU21: Monitorear y Validar Operaciones Clínicas](#41-cu21-monitorear-y-validar-operaciones-clínicas)
5. [Arquitectura del Componente de Monitoreo](#5-arquitectura-del-componente-de-monitoreo)
6. [Implementación en el Código](#6-implementación-en-el-código)
   - 6.1 [`backend/app/monitoring.py`](#61-backendappmonitoringpy--núcleo-del-monitoreo)
   - 6.2 [`backend/app/routes/clinical.py`](#62-backendapproutesclinicalpy--punto-de-intercepción-clínico)
   - 6.3 [`backend/app/auth.py`](#63-backendappauthpy--seguridad-rbac-con-auditoría)
   - 6.4 [`backend/app/main.py`](#64-backendappmainpy--registro-del-middleware-global)
7. [Trazabilidad Requisito → Código](#7-trazabilidad-requisito--código)
8. [Diagrama de Flujo de Intercepción Síncrona](#8-diagrama-de-flujo-de-intercepción-síncrona)
9. [Ejemplos de Logs en Consola Docker](#9-ejemplos-de-logs-en-consola-docker)
10. [Archivos del Sistema](#10-archivos-del-sistema)

---

## 1. ALCANCE TÉCNICO FUNCIONAL

Este módulo provee la **gobernanza, telemetría y auditoría en tiempo real** para el **Motor Antropométrico Clínico** (`POST /api/v1/clinical/calculate`). Actúa de forma síncrona e intercepta el pipeline lógico en el backend de FastAPI antes de realizar la persistencia NoSQL local, asegurando el cumplimiento estricto de las métricas de calidad **ISO 25000**.

El módulo se inyecta en tres puntos del ciclo de vida de la solicitud:

| Capa de intercepción | Momento | Responsabilidad |
|---|---|---|
| **Middleware global** | Antes/después de cualquier ruta | Capturar respuestas HTTP 403 y registrar alertas de seguridad (RF23) |
| **Dependencia RBAC** | Antes de ejecutar el handler | Validar rol del usuario y registrar intentos no autorizados (RF23) |
| **Context manager** | Dentro del handler clínico | Medir latencia del pipeline completo (RF21) y validar seudonimización pre-escritura (RF22) |

---

## 2. ESPECIFICACIÓN DE REQUISITOS DEL SISTEMA

### 2.1 Requisitos Funcionales Añadidos

| ID | Descripción | Implementación |
|---|---|---|
| **RF21** | **Intercepción de Latencia de Cómputo:** El sistema debe registrar síncronamente el tiempo de ejecución de las ecuaciones de IMC e ICC por cada consulta. | `monitoring.py:122–143` — `track_clinical_performance()` mide con `time.perf_counter()` y alerta si ≥ 300 ms |
| **RF22** | **Auditoría de Fugas de Información PII:** El módulo debe validar la estructura del JSON previo a la escritura en base de datos, bloqueando el guardado si detecta datos personales legibles en texto plano. | `monitoring.py:146–170` — `validate_privacy()` escanea llaves del diccionario contra `FORBIDDEN_PII_FIELDS` y lanza `HTTP 400` |
| **RF23** | **Registro de Alertas de Seguridad RBAC:** El sistema debe capturar logs formateados ante fallos de autorización provocados por tokens sin los privilegios del grupo requerido. | `monitoring.py:85–119` (middleware global) + `auth.py:49–66` (`require_role()` con logger) |

### 2.2 Requisitos No Funcionales Relacionados (Métricas ISO 25000)

| ID | Descripción | Implementación |
|---|---|---|
| **RNF1** | **Eficiencia (Tiempo de Respuesta):** El procesamiento del motor matemático y el interceptor de monitoreo no deben superar los 300 ms síncronos en total. | `monitoring.py:138` — umbral `>= 300.0` ms. El context manager envuelve cálculo + persistencia + validación |
| **RNF9** | **Seguridad (Seudonimización Estricta):** Los registros del log de monitoreo histórico no deben almacenar texto plano con datos identificables del paciente, usando únicamente variables enlazadas a un identificador universal `Patient_ID` (UUIDv4). | `routes/clinical.py:98–99` — `patient_id = str(uuid.uuid4())` y `calculation_id = str(uuid.uuid4())`. No se persisten campos PII |

---

## 3. HISTORIAS DE USUARIO

### 3.1 HU-MON-01: Interceptor de Telemetría, Seguridad y Gobernanza de Datos

- **Como:** Docente (Administrador) del Sistema.
- **Quiero:** Que el backend intercepte automáticamente las solicitudes del motor clínico para medir su rendimiento, auditar la seguridad por roles (RBAC) y validar que no existan datos clínicos expuestos.
- **Para:** Garantizar la alta eficiencia de procesamiento del software y asegurar que los logs históricos clínicos cumplan con las normas de privacidad inmutable.

### 3.2 Criterios de Aceptación (Escenarios de Pruebas)

#### Escenario 1: Alerta por degradación de rendimiento técnico (RNF1)

- **Dado que** un estudiante con sesión activa envía un JSON de variables antropométricas al endpoint `/api/v1/clinical/calculate`,
- **Cuando** el motor de FastAPI tarda un tiempo de ejecución síncrono ≥ 300 ms en resolver el IMC o el ICC,
- **Entonces** el interceptor captura la anomalía y dispara una advertencia formateada en la consola de Docker:

```
[WARNING] [PERFORMANCE ALERT] Cómputo antropométrico crítico excedió el límite RNF1. Latencia: 452.10 ms
```

**Cobertura en código:**
- `monitoring.py:138` — condición `if elapsed_ms >= 300.0`
- `routes/clinical.py:43` — `with track_clinical_performance():` envuelve cálculo + persistencia + validación

#### Escenario 2: Bloqueo de persistencia por violación de privacidad de datos de salud (RF22)

- **Dado que** la ruta lógica procesa el cálculo médico y se prepara para persistir el objeto JSON en la base NoSQL local,
- **Cuando** la función de escaneo estructural del monitor detecta llaves con datos personales explícitos (como `'nombre'`, `'cedula'` o `'correo'` del paciente) en lugar de un `Patient_ID` (UUIDv4) anónimo,
- **Entonces** el sistema aborta de forma atómica la transacción, bloquea la escritura local y retorna síncronamente una excepción `HTTP 400 Bad Request`:

```json
HTTP 400 Bad Request
{
  "detail": "Violación de política de privacidad de datos de salud: el campo 'nombre' contiene datos personales identificables del paciente. Persistencia bloqueada."
}
```

**Cobertura en código:**
- `monitoring.py:146–170` — búsqueda de `FORBIDDEN_PII_FIELDS` en las llaves del diccionario
- `routes/clinical.py:126` — llamada a `validate_privacy(log_item)` justo antes de `table.put_item()`

---

## 4. DISEÑO DEL CASO DE USO ICONIX

### 4.1 CU21: Monitorear y Validar Operaciones Clínicas

| Elemento | Descripción |
|---|---|
| **Actor Principal** | Interceptor de Monitoreo (Componente del Sistema) |
| **Actor Secundario** | Controlador de Rutas Clínicas (`clinical.py`) |
| **Objetivo** | Auditar la latencia de cómputo, capturar incidencias de seguridad y forzar la seudonimización de datos en la base NoSQL local de forma síncrona |
| **Precondición** | El endpoint `POST /api/v1/clinical/calculate` debe ser invocado por una petición HTTPS/HTTP entrante que contenga un token JWT |

#### Flujo Principal

| Paso | Acción | Código |
|---|---|---|
| 1 | El interceptor inicia un temporizador de alta precisión al recibir la solicitud en la ruta. | `monitoring.py:133` — `start = time.perf_counter()` |
| 2 | El sistema extrae el payload del token JWT local y valida el rol (`Estudiante` o `Docente`). | `auth.py:49–66` — `require_role(["Estudiantes", "Docentes"])` |
| 3 | El motor de cálculo en Python computa las fórmulas del IMC e ICC. | `routes/clinical.py:44–96` — IMC, ICC, TMB Harris-Benedict, TMB Mifflin-St Jeor, GET |
| 4 | El interceptor detiene el temporizador, calcula la latencia total y evalúa el umbral técnico de 300 ms. | `monitoring.py:137–143` — `elapsed_ms = (time.perf_counter() - start) * 1000.0` |
| 5 | La función de gobernanza de datos escanea las llaves del JSON resultante para verificar que no contenga PII. | `monitoring.py:161–162` — iteración sobre `data.keys()` |
| 6 | Al confirmar la presencia exclusiva del `Patient_ID` (UUIDv4), autoriza síncronamente la escritura atómica en la colección local de auditoría. | `routes/clinical.py:128` — `table.put_item(Item=log_item)` |

#### Flujo Alterno A — Fallo de Rol (RBAC)

- **Condición:** Las claims de rol no corresponden al grupo autorizado.
- **Acción:** El interceptor captura el evento de seguridad y escribe en el log local de auditoría:
  ```
  [SECURITY ALERT] Intento de acceso no autorizado por rol a funciones clínicas. Origen: {email}
  ```
- **Código:** `auth.py:54–60` (logger en `require_role`) + `monitoring.py:100–118` (middleware global)

#### Flujo Alterno B — Fallo de Privacidad

- **Condición:** El escáner del JSON detecta campos de identidad legibles expuestos.
- **Acción:** El componente funcional de monitoreo lanza una excepción `HTTP 400 Bad Request` y bloquea la inserción en la base de datos de persistencia.
- **Código:** `monitoring.py:163–169` — `raise HTTPException(status_code=400)`

#### Postcondición

- El log de auditoría anonimizado queda registrado localmente en la tabla DynamoDB `Auditoria_Planes_Table`.
- Las métricas de rendimiento son validadas en la consola del servidor.

---

## 5. ARQUITECTURA DEL COMPONENTE DE MONITOREO

La inyección de este componente no requiere servicios pesados ni dependencias de nube externas, manteniendo la estructura multi-contenedor limpia y directa:

```
[Frontend SPA: React]
       │
       │ (HTTP/HTTPS síncrono con Token JWT)
       ▼
[FastAPI Router: routes/clinical.py]
       │
       ├───► [SecurityMonitoringMiddleware] ───► Captura HTTP 403 de TODAS las rutas
       │                                         ───► Log: [SECURITY ALERT] ...
       │
       ├───► [require_role()] ───► Valida grupo RBAC (Estudiantes / Docentes)
       │                           ───► Log: [SECURITY ALERT] ... (doble capa)
       │
       ├───► [track_clinical_performance()] ───► Timer alta precisión (perf_counter)
       │     └──► [validate_privacy()] ───► Escanea PII en log_item
       │     └──► [table.put_item()]   ───► Persiste en DynamoDB Local
       │                                   ───► Si ≥300ms → [PERFORMANCE ALERT]
       ▼
[NoSQL Database local: Auditoria_Planes_Table]
       │
       ├── calculation_id  (UUIDv4)    ← Clave primaria HASH
       ├── patient_id      (UUIDv4)    ← Seudónimo del paciente
       ├── imc, icc, tmb, gasto_total  ← Datos clínicos
       └── created_at                  ← Timestamp UTC
```

### Ubicación en el stack del backend

```
main.py
  ├── CORSMiddleware
  ├── SecurityMonitoringMiddleware  ← Capa 1: detección global de 403s
  ├── Router: health.py
  ├── Router: auth.py
  │     └── require_role()          ← Capa 2: alerta de seguridad al denegar acceso
  ├── Router: clinical.py
  │     ├── require_role()          ← Barrera RBAC
  │     ├── track_clinical_performance()  ← Capa 3: medición de latencia
  │     │     ├── Cálculo IMC/ICC/TMB/GET
  │     │     ├── validate_privacy()     ← Capa 4: escáner PII pre-escritura
  │     │     └── DynamoDB put_item
  │     └── Response JSON
  ├── Router: plans.py
  ├── Router: admin.py
  └── database.py
```

---

## 6. IMPLEMENTACIÓN EN EL CÓDIGO

### 6.1 `backend/app/monitoring.py` — Núcleo del Monitoreo

**Ubicación:** `backend/app/monitoring.py` (170 líneas)

```
[PERFORMANCE ALERT] ← track_clinical_performance()   (línea 138)
[SECURITY ALERT]    ← SecurityMonitoringMiddleware    (líneas 106, 112)
HTTP 400            ← validate_privacy()              (línea 163)
```

#### Estructura del archivo

| Componente | Tipo | Líneas | Rol en el sistema |
|---|---|---|---|
| `logger` | `logging.Logger` | 20–28 | Logger central `nutria.monitoring` con formato `[LEVEL] mensaje` |
| `CLINICAL_PATHS` | `set` | 30 | Rutas del endpoint clínico para mensajes específicos |
| `FORBIDDEN_PII_FIELDS` | `set` | 32 | Campos prohibidos: `nombre`, `cedula`, `correo` |
| `_jwks_client` | `PyJWKClient` | 35–44 | Cliente JWKS global para validar tokens Cognito RS256 |
| `_decode_token_from_request()` | función | 47–82 | Decodifica JWT del header `Authorization` con 3 modos de fallback |
| `SecurityMonitoringMiddleware` | clase | 85–119 | Middleware Starlette que captura HTTP 403 de todas las rutas |
| `track_clinical_performance()` | context manager | 122–143 | Mide latencia y alerta si ≥ 300 ms |
| `validate_privacy()` | función | 146–170 | Escanea diccionario y bloquea si encuentra PII |

#### `_decode_token_from_request()` — Modos de decodificación

```
1. JWT local HS256  ──► jwt.decode(token, JWT_SECRET, algorithms=[HS256])
2. Cognito JWKS     ──► PyJWKClient.get_signing_key_from_jwt() + RS256
3. Mock tokens      ──► token == "mock-teacher-token" o "mock-student-token"
4. Falla            ──► retorna {} (desconocido)
```

#### `SecurityMonitoringMiddleware.dispatch()` — Lógica de captura

```python
async def dispatch(self, request: Request, call_next):
    response = await call_next(request)

    if response.status_code == 403:
        payload = _decode_token_from_request(request)
        email = payload.get("email", "desconocido")

        if request.method == "POST" and request.url.path in CLINICAL_PATHS:
            # "[SECURITY ALERT] Intento de acceso no autorizado por rol a funciones clínicas. Origen: {email}"
        else:
            # "[SECURITY ALERT] Acceso denegado (HTTP 403) — Ruta: {method} {path} | Origen: {email}"

    return response
```

#### `track_clinical_performance()` — Medición de latencia

```python
@contextmanager
def track_clinical_performance():
    start = time.perf_counter()
    try:
        yield                          # ← Aquí se ejecuta el handler completo
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if elapsed_ms >= 300.0:
            logger.warning(
                "[PERFORMANCE ALERT] Cómputo antropométrico crítico excedió "
                "el límite RNF1. Latencia: %.2f ms", elapsed_ms
            )
```

#### `validate_privacy()` — Escáner de PII

```python
def validate_privacy(data: Dict[str, Any]) -> None:
    for key in data:
        if isinstance(key, str) and key.strip().lower() in FORBIDDEN_PII_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Violación de política de privacidad de datos de salud: "
                    f"el campo '{key}' contiene datos personales identificables "
                    "del paciente. Persistencia bloqueada."
                )
            )
```

---

### 6.2 `backend/app/routes/clinical.py` — Punto de Intercepción Clínico

**Ubicación:** `backend/app/routes/clinical.py` (146 líneas)

#### Modelos Pydantic

| Modelo | Líneas | Campos |
|---|---|---|
| `ClinicalCalculateRequest` | 13–21 | `peso_kg`, `estatura_m`, `perimetro_cintura_cm`, `perimetro_cadera_cm`, `sexo_biologico`, `edad`, `factor_actividad`, `efecto_termogenico` |
| `ClinicalCalculateResponse` | 23–32 | `imc`, `imc_clasificacion`, `icc`, `icc_riesgo`, `distribucion_grasa`, `tmb_harris`, `tmb_mifflin`, `gasto_total_harris`, `gasto_total_mifflin` |

#### Endpoint: `POST /clinical/calculate`

```python
@router.post("/clinical/calculate", response_model=ClinicalCalculateResponse)
async def calculate_clinical(
    req: ClinicalCalculateRequest,
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))  # ← RBAC + log
):
```

#### Flujo interno del handler

| Paso | Líneas | Descripción |
|---|---|---|
| Validación de sexo | 39–41 | `sexo_biologico` debe ser `Masculino` o `Femenino` |
| **`with track_clinical_performance():`** | **43** | **Inicia timer. Mide TODO lo que sigue.** |
| Cálculo de IMC | 44–53 | `peso_kg / estatura_m²` + clasificación WHO |
| Cálculo de ICC | 55–76 | `cintura / cadera` + riesgo según sexo |
| Cálculo de TMB Harris-Benedict | 80–83 | Fórmula según sexo |
| Cálculo de TMB Mifflin-St Jeor | 85–88 | Fórmula según sexo |
| Cálculo de GET | 90–91 | `TMB × factor_actividad × (1 + efecto_termogenico/100)` |
| Redondeo | 93–96 | `round(valor, 2)` |
| **Generación de UUIDs** | **98–99** | `calculation_id = str(uuid.uuid4())`, `patient_id = str(uuid.uuid4())` **(RNF9)** |
| Obtención de tabla DynamoDB | 102 | `get_or_create_auditoria_table()` |
| Construcción de `log_item` | 103–124 | Diccionario completo con todos los campos clínicos + `created_at` |
| **`validate_privacy(log_item)`** | **126** | **Escáner PII pre-escritura (RF22)** |
| `table.put_item(Item=log_item)` | 128 | Persistencia en `Auditoria_Planes_Table` |
| Manejo de error DynamoDB | 129–134 | Captura `ClientError` y retorna HTTP 500 |
| **Fin del `with`** | — | Se evalúa latencia. Si ≥ 300 ms → `[PERFORMANCE ALERT]` |
| Retorno de respuesta | 136–146 | `ClinicalCalculateResponse` |

#### Esquema del `log_item` persistido en DynamoDB

```python
{
    "calculation_id": "a1b2c3d4-...",        # UUIDv4 (HASH key)
    "patient_id": "e5f6g7h8-...",            # UUIDv4 (seudónimo)
    "peso_kg": Decimal("70.5"),
    "estatura_m": Decimal("1.75"),
    "perimetro_cintura_cm": Decimal("85.0"),
    "perimetro_cadera_cm": Decimal("95.0"),
    "sexo_biologico": "Masculino",
    "edad": 25,
    "factor_actividad": Decimal("1.55"),
    "efecto_termogenico": Decimal("10.0"),
    "imc": Decimal("23.02"),
    "imc_clasificacion": "Normal",
    "icc": Decimal("0.89"),
    "icc_riesgo": "Bajo",
    "distribucion_grasa": "Ginecoide (Pera)",
    "tmb_harris": Decimal("1725.45"),
    "tmb_mifflin": Decimal("1690.50"),
    "gasto_total_harris": Decimal("2942.89"),
    "gasto_total_mifflin": Decimal("2882.30"),
    "created_at": "2026-06-24T12:00:00.000000"
}
```

> **Nota:** No existe ningún campo `nombre`, `cedula` ni `correo`. El paciente solo es identificable mediante `patient_id` (UUIDv4). Esto cumple RNF9.

---

### 6.3 `backend/app/auth.py` — Seguridad RBAC con Auditoría

**Ubicación:** `backend/app/auth.py` (66 líneas)

#### `require_role()` — Dependencia de autorización con logging

```python
def require_role(allowed_groups: list):
    def dependency(user: dict = Depends(get_current_user)):
        groups = user.get("cognito:groups", [])
        if not groups:
            groups = ["Estudiantes"]                  # ← default por seguridad
        if not any(g in allowed_groups for g in groups):
            email = user.get("email", "desconocido")
            logger.warning(
                "[SECURITY ALERT] Intento de acceso no autorizado por rol "
                "a funciones clínicas. Origen: %s", email
            )
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere pertenecer a uno de los grupos: {allowed_groups}"
            )
        return user
    return dependency
```

| Aspecto | Detalle |
|---|---|
| **Doble capa de logging** | `require_role()` registra el alerta al momento del `raise`. Adicionalmente, `SecurityMonitoringMiddleware` captura la respuesta 403 y vuelve a registrar. |
| **Logger compartido** | Usa `logging.getLogger("nutria.monitoring")` para mantener formato homogéneo con el middleware. |
| **Grupo por defecto** | Si el token no trae `cognito:groups`, se asigna `["Estudiantes"]` como fallback seguro. |

#### `get_current_user()` — Validación de tokens (dos niveles)

| Nivel | Método | Algoritmo |
|---|---|---|
| 1 | Decodificación local | `jwt.decode(token, JWT_SECRET, HS256)` |
| 2 | Validación Cognito | `PyJWKClient` + RS256 con `audience` e `issuer` |
| 3 | Tokens mock | `mock-teacher-token` → `Docentes`, `mock-student-token` → `Estudiantes` |

---

### 6.4 `backend/app/main.py` — Registro del Middleware Global

**Ubicación:** `backend/app/main.py` (38 líneas)

```python
from app.monitoring import SecurityMonitoringMiddleware

app = FastAPI(title="NUTRIA - API Motor Antropométrico")

app.add_middleware(CORSMiddleware, ...)

app.add_middleware(SecurityMonitoringMiddleware)     # ← Línea 21: registro del middleware

app.include_router(health.router)
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(clinical.router)                  # ← El middleware protege todas las rutas

# También registradas con prefijo /api/v1
app.include_router(plans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")
```

**Orden de los middlewares:**
1. `CORSMiddleware` — Permite orígenes cruzados
2. `SecurityMonitoringMiddleware` — **Monitoreo de seguridad**: captura cualquier HTTP 403 post-procesamiento

---

## 7. TRAZABILIDAD REQUISITO → CÓDIGO

| ID | Tipo | Descripción | Archivo | Líneas | Estado |
|---|---|---|---|---|---|
| RF21 | Funcional | Intercepción de latencia de cómputo IMC/ICC | `monitoring.py` | 122–143 | ✅ |
| | | | `routes/clinical.py` | 43 | ✅ |
| RF22 | Funcional | Auditoría de fugas PII (bloqueo pre-escritura) | `monitoring.py` | 146–170 | ✅ |
| | | | `routes/clinical.py` | 126 | ✅ |
| RF23 | Funcional | Registro de alertas de seguridad RBAC | `monitoring.py` | 85–119 | ✅ |
| | | | `auth.py` | 49–66 | ✅ |
| | | | `main.py` | 21 | ✅ |
| RNF1 | No Funcional | Eficiencia — límite 300 ms | `monitoring.py` | 133–143 | ✅ |
| RNF9 | No Funcional | Seudonimización estricta (UUIDv4) | `routes/clinical.py` | 98–99 | ✅ |

### Cobertura por archivo

| Archivo | Líneas totales | Líneas de monitoreo | % |
|---|---|---|---|
| `backend/app/monitoring.py` | 170 | 170 (archivo completo) | 100% |
| `backend/app/routes/clinical.py` | 146 | ~104 (líneas 43–134) | 71% |
| `backend/app/auth.py` | 66 | ~9 (líneas 54–62) | 14% |
| `backend/app/main.py` | 38 | 1 (línea 21) | 3% |

---

## 8. DIAGRAMA DE FLUJO DE INTERCEPCIÓN SÍNCRONA

```
CLIENTE (React SPA)
  │
  │ POST /api/v1/clinical/calculate
  │ Authorization: Bearer <JWT>
  │ Body: { peso_kg, estatura_m, ... }
  ▼
┌──────────────────────────────────────────────────────────────────┐
│ ❶ SecurityMonitoringMiddleware.dispatch()                        │
│   (Se ejecuta antes y después de la ruta)                        │
│                                                                  │
│   call_next(request) ──────────────────────────────────────────┐ │
└───────────────────────────────────────────────────────────────────┘
                                                                    │
┌──────────────────────────────────────────────────────────────────┐ │
│ ❷ require_role(["Estudiantes", "Docentes"])                     │ │
│                                                                  │ │
│   get_current_user()                                             │ │
│     ├─ JWT decode local (HS256)                                  │ │
│     ├─ JWT decode Cognito (RS256)                                │ │
│     └─ Mock tokens (desarrollo)                                  │ │
│                                                                  │ │
│   ¿cognito:groups ∩ allowed_groups?                              │ │
│     ├─ NO → log [SECURITY ALERT] + HTTP 403 ◄─────────────────┐ │ │
│     └─ SÍ → retorna user payload                              │ │ │
└───────────────────────────────────────────────────────────────────┘ │
                                                                      │
┌───────────────────────────────────────────────────────────────────┐ │
│ ❸ track_clinical_performance() — INICIO TIMER                     │ │
│   start = time.perf_counter()                                     │ │
│                                                                   │ │
│   ├── Validación sexo_biologico                                   │ │
│   ├── Cálculo IMC + clasificación                                 │ │
│   ├── Cálculo ICC + riesgo + distribución grasa                   │ │
│   ├── Cálculo TMB Harris-Benedict                                 │ │
│   ├── Cálculo TMB Mifflin-St Jeor                                 │ │
│   ├── Cálculo GET (× factor_actividad × efecto_termogenico)       │ │
│   ├── Generación calculation_id (UUIDv4)                          │ │
│   ├── Generación patient_id (UUIDv4)         ← RNF9               │ │
│   ├── Construcción log_item                                       │ │
│   ├── validate_privacy(log_item)                                  │ │
│   │     └── ¿PII detectado?                                       │ │
│   │           ├─ SÍ → HTTP 400 Bad Request ◄──────────────────┐ │ │
│   │           └─ NO → continúa                                 │ │ │
│   ├── table.put_item(Item=log_item)         ← DinamoDB Local    │ │
│   └── [posibles excepciones ClientError → HTTP 500]              │ │
│                                                                   │ │
│ ❸ track_clinical_performance() — FIN TIMER                       │ │
│   elapsed_ms = (perf_counter - start) × 1000                     │ │
│   ¿elapsed_ms ≥ 300?                                             │ │
│     ├─ SÍ → log [PERFORMANCE ALERT]                              │ │
│     └─ NO → OK                                                   │ │
└───────────────────────────────────────────────────────────────────┘ │
                                                                      │
┌──────────────────────────────────────────────────────────────────┐ │
│ ❹ Respuesta HTTP 200 OK                                        ◄┘ │
│   Body: { imc, icc, tmb_harris, tmb_mifflin, ... }               │
└─────────────────────────────────────────────────────────────────────┘
                                                                      
┌──────────────────────────────────────────────────────────────────┐
│ ❶ SecurityMonitoringMiddleware.dispatch() — POST-PROCESAMIENTO   │
│                                                                  │
│   ¿response.status_code == 403?                                  │
│     ├─ SÍ → log [SECURITY ALERT]                                │
│     └─ NO → OK                                                  │
└──────────────────────────────────────────────────────────────────┘
  │
  ▼
CLIENTE ← HTTP Response
```

---

## 9. EJEMPLOS DE LOGS EN CONSOLA DOCKER

### Operación exitosa (latencia normal, sin incidentes)

```
[INFO]    Cálculo antropométrico completado. Usuario: estudiante_prueba
```

### Alerta de rendimiento (RNF1)

```
[WARNING] [PERFORMANCE ALERT] Cómputo antropométrico crítico excedió el límite RNF1. Latencia: 452.10 ms
```

### Alerta de seguridad por RBAC (RF23) — desde middleware

```
[WARNING] [SECURITY ALERT] Intento de acceso no autorizado por rol a funciones clínicas. Origen: alumno@test.com
```

### Alerta de seguridad por RBAC (RF23) — desde require_role (doble capa)

```
[WARNING] [SECURITY ALERT] Intento de acceso no autorizado por rol a funciones clínicas. Origen: alumno@test.com
```

### Alerta de seguridad genérica (cualquier endpoint, no clínico)

```
[WARNING] [SECURITY ALERT] Acceso denegado (HTTP 403) — Ruta: GET /admin/tasks | Origen: estudiante@test.com
```

### Bloqueo por violación de privacidad (RF22)

```
HTTP 400 Bad Request
{
  "detail": "Violación de política de privacidad de datos de salud: el campo 'nombre' contiene datos personales identificables del paciente. Persistencia bloqueada."
}
```

### Error de persistencia DynamoDB

```
[ERROR]   Error persisting calculation in DynamoDB: ...
HTTP 500 Internal Server Error
{
  "detail": "Error al guardar auditoría en base de datos: ..."
}
```

---

## 10. ARCHIVOS DEL SISTEMA

### Archivos modificados

| Archivo | Líneas | Cambio principal |
|---|---|---|
| `backend/app/monitoring.py` | 170 | `_decode_token_from_request()` con fallback Cognito JWKS + mock tokens; `SecurityMonitoringMiddleware` expandido a todas las rutas HTTP 403 |
| `backend/app/routes/clinical.py` | 146 | `track_clinical_performance()` envuelve todo el handler (cálculo + persistencia + validación) |
| `backend/app/auth.py` | 66 | `require_role()` registra `[SECURITY ALERT]` antes de lanzar HTTP 403 |

### Archivos creados

| Archivo | Propósito |
|---|---|
| `MONITOREO.md` | Este documento de trazabilidad y especificación completa |

### Archivos no modificados (existentes y relevantes)

| Archivo | Rol en el sistema |
|---|---|
| `backend/app/main.py` | Punto de entrada de FastAPI. Registra `SecurityMonitoringMiddleware` en línea 21 |
| `backend/app/config.py` | Variables de entorno: `JWT_SECRET`, `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, `AWS_REGION` |
| `backend/app/database.py` | Fábrica de recursos DynamoDB. Crea `Auditoria_Planes_Table` con HASH key `calculation_id` |
| `backend/requirements.txt` | Dependencias: `fastapi`, `pyjwt`, `boto3`, `python-dotenv` |
| `docker-compose.yml` | Orquesta `dynamodb-local`, `fastapi-backend`, `react-frontend` |

---

*Documento generado a partir del código fuente del proyecto NUTRIA. Junio 2026.*
