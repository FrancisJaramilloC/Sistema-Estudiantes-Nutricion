"""
M\u00f3dulo de Monitoreo Funcional S\u00edncrono para el endpoint POST /api/v1/clinical/calculate.

Implementa tres controles obligatorios seg\u00fan el Documento de Requisitos:
  1. RNF1 - Eficiencia: Medici\u00f3n de latencia de c\u00e1lculo antropom\u00e9trico (l\u00edmite 300 ms).
  2. RBAC - Seguridad: Detecci\u00f3n de intentos de acceso no autorizado (HTTP 403).
  3. ISO 25000 - Privacidad: Validaci\u00f3n de seudonimizaci\u00f3n en datos de auditor\u00eda m\u00e9dica.
"""

import time
import jwt
import logging
from contextlib import contextmanager
from typing import Any, Dict
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app import config

logger = logging.getLogger("nutria.monitoring")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(message)s"
    ))
    logger.addHandler(handler)

CLINICAL_PATHS = {"/clinical/calculate", "/api/v1/clinical/calculate"}

FORBIDDEN_PII_FIELDS = {"nombre", "cedula", "correo"}


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
        return jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
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
    elif token == "mock-student-token":
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
            payload = _decode_token_from_request(request)
            email = payload.get("email", "desconocido")

            if request.method == "POST" and request.url.path in CLINICAL_PATHS:
                logger.warning(
                    "[SECURITY ALERT] Intento de acceso no autorizado por rol "
                    "a funciones clínicas. Origen: %s",
                    email,
                )
            else:
                logger.warning(
                    "[SECURITY ALERT] Acceso denegado (HTTP 403) — "
                    "Ruta: %s %s | Origen: %s",
                    request.method,
                    request.url.path,
                    email,
                )

        return response


@contextmanager
def track_clinical_performance():
    """
    Context manager que mide la latencia del bloque de c\u00e1lculos
    antropom\u00e9tricos (IMC, ICC, TMB, GET).

    Si la latencia supera los 300 ms, registra una alerta de rendimiento
    en los logs de Docker.

    Requisito: RNF1 - Tiempo de Respuesta de Consulta (< 300 ms).
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if elapsed_ms >= 300.0:
            logger.warning(
                "[PERFORMANCE ALERT] C\u00f3mputo antropom\u00e9trico cr\u00edtico excedi\u00f3 "
                "el l\u00edmite RNF1. Latencia: %.2f ms",
                elapsed_ms,
            )


def validate_privacy(data: Dict[str, Any]) -> None:
    """
    Escanea estructuralmente las llaves del diccionario ``data`` en busca
    de campos que contengan datos personales identificables del paciente.

    Campos prohibidos (ISO 25000 - Seudonimizaci\u00f3n):
      - 'nombre'
      - 'cedula'
      - 'correo'

    Si se detecta alguno, se bloquea la escritura y se lanza una excepci\u00f3n
    HTTP 400 Bad Request.

    Requisito: Validador Funcional de Privacidad y Seudonimizaci\u00f3n.
    """
    for key in data:
        if isinstance(key, str) and key.strip().lower() in FORBIDDEN_PII_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Violaci\u00f3n de pol\u00edtica de privacidad de datos de salud: "
                    f"el campo '{key}' contiene datos personales identificables "
                    "del paciente. Persistencia bloqueada."
                ),
            )
