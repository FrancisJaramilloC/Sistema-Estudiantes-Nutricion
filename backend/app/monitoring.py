"""
Módulo de Monitoreo Funcional Síncrono para el endpoint POST /api/v1/clinical/calculate.

Implementa tres controles obligatorios según el Documento de Requisitos:
  1. RNF1 - Eficiencia: Medición de latencia de cálculo antropométrico (límite 300 ms).
  2. RBAC - Seguridad: Detección de intentos de acceso no autorizado (HTTP 403).
  3. ISO 25000 - Privacidad: Validación de seudonimización en datos de auditoría médica.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict

import jwt
from fastapi import HTTPException
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app import config

logger = logging.getLogger("nutria.monitoring")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)

CLINICAL_PATHS = {"/clinical/calculate", "/api/v1/clinical/calculate"}
FORBIDDEN_PII_FIELDS = {"nombre", "cedula", "correo"}

CLINICAL_LATENCY_SECONDS = Histogram(
    "nutria_clinical_latency_seconds",
    "Latencia del pipeline de cálculos clínicos en segundos",
)
CLINICAL_REQUESTS_TOTAL = Counter(
    "nutria_clinical_requests_total",
    "Total de cálculos clínicos completados",
)
HTTP_403_TOTAL = Counter(
    "nutria_http_403_total",
    "Total de respuestas HTTP 403 observadas por el middleware de monitoreo",
)
RBAC_DENIALS_TOTAL = Counter(
    "nutria_rbac_denials_total",
    "Total de denegaciones de acceso basado en roles en rutas clínicas",
)
PRIVACY_BLOCKS_TOTAL = Counter(
    "nutria_privacy_blocks_total",
    "Total de escrituras bloqueadas por fallos en validación de privacidad",
)
DB_PERSISTENCE_ERRORS_TOTAL = Counter(
    "nutria_db_persistence_errors_total",
    "Total de errores de persistencia en base de datos en registro clínico",
)

LOGIN_SUCCESS_TOTAL = Counter(
    "nutria_login_success_total",
    "Total de inicios de sesión exitosos",
)

def log_login_event(username: str):
    """
    Registra un evento de inicio de sesión exitoso.
    Se emite como log estructurado (visible en Grafana Cloud Logs vía Loki)
    e incrementa el contador de métricas correspondiente.
    """
    LOGIN_SUCCESS_TOTAL.inc()
    logger.info(
        "[LOGIN] Usuario autenticado exitosamente | username=%s",
        username,
    )

_jwks_client = None
if config.COGNITO_USER_POOL_ID and not config.COGNITO_USER_POOL_ID.startswith("mock") and config.COGNITO_USER_POOL_ID != "":
    try:
        jwks_url = (
            f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/"
            f"{config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )
        _jwks_client = jwt.PyJWKClient(jwks_url)
    except Exception:
        _jwks_client = None


def _decode_token_from_request(request: Request) -> Dict[str, Any]:
    """Decodifica el JWT desde el encabezado Authorization sin lanzar excepciones."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return {}
    token = auth[7:]

    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except Exception:
        pass

    if _jwks_client and config.COGNITO_USER_POOL_ID:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=config.COGNITO_APP_CLIENT_ID,
                issuer=(
                    f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/"
                    f"{config.COGNITO_USER_POOL_ID}"
                ),
            )
        except Exception:
            pass

    if token == "mock-teacher-token":
        return {"username": "docente_prueba", "cognito:groups": ["Docentes"]}
    if token == "mock-student-token":
        return {"username": "estudiante_prueba", "cognito:groups": ["Estudiantes"]}

    return {}


class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware global que detecta respuestas HTTP 403 Forbidden y registra
    una alerta de seguridad con el correo electrónico del usuario que originó
    la solicitud.

    En endpoints clínicos el mensaje es específico; en el resto de rutas se
    registra el origen y la ruta afectada.

    Requisito: RF23 — Registro de Alertas de Seguridad RBAC.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if response.status_code == 403:
            HTTP_403_TOTAL.inc()
            payload = _decode_token_from_request(request)
            email = payload.get("email", "desconocido")

            if request.method == "POST" and request.url.path in CLINICAL_PATHS:
                logger.warning(
                    "[SECURITY ALERT] Intento de acceso no autorizado por rol a funciones clínicas. Origen: %s",
                    email,
                )
            else:
                logger.warning(
                    "[SECURITY ALERT] Acceso denegado (HTTP 403) — Ruta: %s %s | Origen: %s",
                    request.method,
                    request.url.path,
                    email,
                )

        return response


@contextmanager
def track_clinical_performance():
    """
    Context manager que mide la latencia del bloque de cálculos
    antropométricos (IMC, ICC, TMB, GET).

    Si la latencia supera los 300 ms, registra una alerta de rendimiento
    en los logs de Docker.

    Requisito: RNF1 - Tiempo de Respuesta de Consulta (< 300 ms).
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        CLINICAL_LATENCY_SECONDS.observe(elapsed_ms / 1000.0)
        if elapsed_ms >= 300.0:
            logger.warning(
                "[PERFORMANCE ALERT] Cómputo antropométrico crítico excedió el límite RNF1. Latencia: %.2f ms",
                elapsed_ms,
            )


def validate_privacy(data: Dict[str, Any]) -> None:
    """
    Escanea estructuralmente las llaves del diccionario ``data`` en busca
    de campos que contengan datos personales identificables del paciente.

    Campos prohibidos (ISO 25000 - Seudonimización):
      - 'nombre'
      - 'cedula'
      - 'correo'

    Si se detecta alguno, se bloquea la escritura y se lanza una excepción
    HTTP 400 Bad Request.

    Requisito: Validador Funcional de Privacidad y Seudonimización.
    """
    for key in data:
        if isinstance(key, str) and key.strip().lower() in FORBIDDEN_PII_FIELDS:
            PRIVACY_BLOCKS_TOTAL.inc()
            raise HTTPException(
                status_code=400,
                detail=(
                    "Violación de política de privacidad de datos de salud: "
                    f"el campo '{key}' contiene datos personales identificables del paciente. Persistencia bloqueada."
                ),
            )
