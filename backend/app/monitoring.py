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
        return {}


class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware global que detecta respuestas HTTP 403 Forbidden sobre el
    endpoint de c\u00e1lculo cl\u00ednico y registra una alerta de seguridad con el
    correo electr\u00f3nico del usuario que origin\u00f3 la solicitud.

    Requisito: Monitoreo de Seguridad de Accesos (Control RBAC).
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method == "POST" and request.url.path in CLINICAL_PATHS:
            if response.status_code == 403:
                payload = _decode_token_from_request(request)
                email = payload.get("email", "desconocido")
                logger.warning(
                    "[SECURITY ALERT] Intento de acceso no autorizado por rol "
                    "a funciones cl\u00ednicas. Origen: %s",
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
