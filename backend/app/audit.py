"""
Módulo de Auditoría Completa (RNF9)
Registra todas las acciones relevantes del sistema con seudonimización.
"""
import uuid
import hashlib
import logging
from datetime import datetime
from app.database import get_or_create_audit_log_table

logger = logging.getLogger("nutria.audit")


def pseudonymize_actor(actor_id: str) -> str:
    """Genera un ID seudonimizado para datos sensibles (RNF9)."""
    return hashlib.sha256(f"nutria-audit-{actor_id}".encode()).hexdigest()[:16]


def log_audit_event(
    actor_id: str,
    accion: str,
    entidad: str,
    entidad_id: str = None,
    resultado: str = "exito",
    detalle: str = None,
    sensitive_data: bool = False,
):
    """
    Registra un evento de auditoría completo en la tabla audit_log.
    
    Args:
        actor_id: ID del usuario que realizó la acción
        accion: Tipo de acción (CREATE, UPDATE, DELETE, LOGIN, etc.)
        entidad: Entidad afectada (paciente, plan, alimento, usuario, etc.)
        entidad_id: ID de la entidad afectada
        resultado: resultado de la operación (exito, fallo)
        detalle: Descripción del cambio (antes/después si aplica)
        sensitive_data: Si es True, seudonimiza el actor_id
    """
    try:
        table = get_or_create_audit_log_table()
        actor_display = pseudonymize_actor(actor_id) if sensitive_data else actor_id
        timestamp = datetime.utcnow().isoformat()

        event = {
            "username": actor_display,
            "timestamp": timestamp,
            "event_id": str(uuid.uuid4()),
            "event_type": accion,
            "entidad": entidad,
            "entidad_id": entidad_id,
            "success": resultado == "exito",
            "reason": detalle or "",
            "actor_original": actor_id if not sensitive_data else None,
        }

        table.put_item(Item=event)
        logger.info(
            "[AUDIT] %s %s → %s (%s) | actor=%s | %s",
            accion, entidad, entidad_id or "N/A",
            resultado, actor_display, detalle or ""
        )
    except Exception as e:
        logger.error("Error registrando evento de auditoría: %s", e)


def log_login_event_detailed(username: str, success: bool, reason: str = ""):
    """Registra eventos de login con detalle completo."""
    log_audit_event(
        actor_id=username,
        accion="LOGIN_SUCCESS" if success else "LOGIN_FAILED",
        entidad="auth",
        entidad_id=username,
        resultado="exito" if success else "fallo",
        detalle=reason,
    )


def log_patient_event(actor_id: str, accion: str, paciente_id: str, detalle: str = None):
    """Registra eventos de pacientes."""
    log_audit_event(
        actor_id=actor_id,
        accion=accion,
        entidad="paciente",
        entidad_id=paciente_id,
        detalle=detalle,
    )


def log_plan_event(actor_id: str, accion: str, plan_id: str, detalle: str = None):
    """Registra eventos de planes alimenticios."""
    log_audit_event(
        actor_id=actor_id,
        accion=accion,
        entidad="plan_alimenticio",
        entidad_id=plan_id,
        detalle=detalle,
    )


def log_user_event(actor_id: str, accion: str, target_user: str, detalle: str = None):
    """Registra eventos de usuarios y roles."""
    log_audit_event(
        actor_id=actor_id,
        accion=accion,
        entidad="usuario",
        entidad_id=target_user,
        detalle=detalle,
    )


def log_report_event(actor_id: str, report_type: str, detalle: str = None):
    """Registra generación/descarga de reportes."""
    log_audit_event(
        actor_id=actor_id,
        accion="GENERAR_REPORTE",
        entidad="reporte",
        entidad_id=report_type,
        detalle=detalle,
    )


def log_device_event(actor_id: str, accion: str, device_id: str, detalle: str = None):
    """Registra eventos de dispositivos IoT."""
    log_audit_event(
        actor_id=actor_id,
        accion=accion,
        entidad="dispositivo",
        entidad_id=device_id,
        detalle=detalle,
        sensitive_data=True,
    )
