import uuid
import hashlib
import re
import secrets
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from app.database import get_dynamodb_resource, convert_decimals
from app.auth import get_current_user, require_role

logger = logging.getLogger("nutria.monitoring")
router = APIRouter(tags=["devices"])


# ==================== MODELOS ====================

class DeviceRegisterRequest(BaseModel):
    student_id: str
    nombre: str = Field(default="ESP32 Cardiaco")


class DeviceRegisterResponse(BaseModel):
    device_id: str
    api_key: str
    student_id: str
    nombre: str
    mensaje: str


class DeviceAutoRegisterRequest(BaseModel):
    mac_address: str = Field(
        ...,
        pattern=r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',
        description="Dirección MAC del dispositivo (formato XX:XX:XX:XX:XX:XX)"
    )
    student_id: str
    nombre: str = Field(default="ESP32 Cardiaco")


class HeartRateReading(BaseModel):
    bpm: int = Field(ge=30, le=220)
    timestamp: str


class HeartRateReadingResponse(BaseModel):
    reading_id: str
    device_id: str
    student_id: str
    bpm: int
    timestamp: str
    created_at: str


# ==================== UTILIDADES DE AUTENTICACIÓN ====================

def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _normalize_mac(mac: str) -> str:
    """Normaliza una dirección MAC a mayúsculas."""
    return mac.upper().strip()


def _find_device_by_mac(devices_table, mac_address: str):
    """Busca un dispositivo por su dirección MAC."""
    response = devices_table.scan(
        FilterExpression="mac_address = :m",
        ExpressionAttributeValues={":m": mac_address}
    )
    items = response.get("Items", [])
    return items[0] if items else None


async def verify_api_key(x_api_key: str = Header(..., alias="X-Api-Key")):
    """Verifica un dispositivo por API Key (método legacy)."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key requerida")
    key_hash = _hash_api_key(x_api_key)
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    response = devices_table.scan(
        FilterExpression="api_key = :k",
        ExpressionAttributeValues={":k": key_hash}
    )
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=401, detail="API Key inválida")
    device = items[0]
    if not device.get("activo", True):
        raise HTTPException(status_code=403, detail="Dispositivo desactivado")
    return device


async def verify_device_mac(x_device_mac: str = Header(..., alias="X-Device-Mac")):
    """Verifica un dispositivo por dirección MAC."""
    if not x_device_mac:
        raise HTTPException(status_code=401, detail="MAC del dispositivo requerida")

    mac = _normalize_mac(x_device_mac)
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    device = _find_device_by_mac(devices_table, mac)
    if not device:
        raise HTTPException(status_code=401, detail="Dispositivo no registrado")
    if not device.get("activo", True):
        raise HTTPException(status_code=403, detail="Dispositivo desactivado")
    return device


async def verify_device(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    x_device_mac: Optional[str] = Header(None, alias="X-Device-Mac")
):
    """
    Verifica un dispositivo usando API Key O dirección MAC.
    Soporta ambos métodos de autenticación para compatibilidad.
    """
    if x_api_key:
        return await verify_api_key(x_api_key)
    elif x_device_mac:
        return await verify_device_mac(x_device_mac)
    else:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación: X-Api-Key o X-Device-Mac"
        )


# ==================== ENDPOINTS ====================

@router.post("/devices/register", response_model=DeviceRegisterResponse)
def register_device(
    req: DeviceRegisterRequest,
    user: dict = Depends(require_role(["Docentes"]))
):
    """Registra un dispositivo manualmente (docente). Genera API Key."""
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    device_id = str(uuid.uuid4())
    api_key = secrets.token_urlsafe(32)
    key_hash = _hash_api_key(api_key)
    now = datetime.now(timezone.utc).isoformat()

    devices_table.put_item(Item={
        "device_id": device_id,
        "api_key": key_hash,
        "student_id": req.student_id,
        "nombre": req.nombre or "ESP32 Cardiaco",
        "activo": True,
        "auth_type": "api_key",
        "created_at": now
    })

    logger.info(
        "[DEVICE] Dispositivo registrado (API Key): %s (estudiante: %s)",
        device_id, req.student_id
    )

    return DeviceRegisterResponse(
        device_id=device_id,
        api_key=api_key,
        student_id=req.student_id,
        nombre=req.nombre or "ESP32 Cardiaco",
        mensaje="Dispositivo registrado exitosamente. Guarda esta API Key, no se mostrará de nuevo."
    )


@router.post("/devices/auto-register")
def auto_register_device(req: DeviceAutoRegisterRequest):
    """
    Auto-registra un dispositivo usando su dirección MAC.
    No requiere autenticación (es llamado por el ESP32 directamente).
    Es idempotente: si el dispositivo ya existe, devuelve su info.
    """
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    mac = _normalize_mac(req.mac_address)

    # Verificar si ya existe un dispositivo con esta MAC
    existing = _find_device_by_mac(devices_table, mac)
    if existing:
        logger.info(
            "[DEVICE] Dispositivo ya registrado por MAC: %s (estudiante: %s)",
            existing["device_id"], existing["student_id"]
        )
        return {
            "device_id": existing["device_id"],
            "mac_address": mac,
            "student_id": existing["student_id"],
            "nombre": existing.get("nombre", "ESP32 Cardiaco"),
            "activo": existing.get("activo", True),
            "mensaje": "Dispositivo ya estaba registrado."
        }

    # Registrar nuevo dispositivo
    device_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    devices_table.put_item(Item={
        "device_id": device_id,
        "mac_address": mac,
        "student_id": req.student_id,
        "nombre": req.nombre or "ESP32 Cardiaco",
        "activo": True,
        "auth_type": "mac",
        "created_at": now
    })

    logger.info(
        "[DEVICE] Dispositivo auto-registrado por MAC: %s (MAC: %s, estudiante: %s)",
        device_id, mac, req.student_id
    )

    return {
        "device_id": device_id,
        "mac_address": mac,
        "student_id": req.student_id,
        "nombre": req.nombre or "ESP32 Cardiaco",
        "activo": True,
        "mensaje": "Dispositivo registrado exitosamente por MAC."
    }


@router.post("/devices/reading")
def receive_reading(
    reading: HeartRateReading,
    device: dict = Depends(verify_device)
):
    """Recibe una lectura de ritmo cardíaco. Acepta auth por API Key o MAC."""
    db = get_dynamodb_resource()
    heart_table = db.Table("heart_rate_readings")

    reading_id = str(uuid.uuid4())
    student_id = device["student_id"]
    now = datetime.now(timezone.utc).isoformat()

    try:
        ts = datetime.fromisoformat(reading.timestamp)
        ts_now = datetime.now(timezone.utc)
        if ts > ts_now:
            raise HTTPException(status_code=400, detail="El timestamp no puede ser futuro")
        diff_hours = abs((ts_now - ts).total_seconds()) / 3600
        if diff_hours > 24:
            raise HTTPException(status_code=400, detail="El timestamp es muy antiguo (>24h)")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de timestamp inválido. Use ISO 8601.")

    heart_table.put_item(Item={
        "student_id": student_id,
        "timestamp": reading.timestamp,
        "reading_id": reading_id,
        "device_id": device["device_id"],
        "bpm": reading.bpm,
        "created_at": now
    })

    logger.info(
        "[HEART_RATE] Lectura registrada: device=%s, student=%s, bpm=%d",
        device["device_id"], student_id, reading.bpm
    )

    return {
        "reading_id": reading_id,
        "device_id": device["device_id"],
        "student_id": student_id,
        "bpm": reading.bpm,
        "timestamp": reading.timestamp,
        "created_at": now,
        "mensaje": "Lectura registrada exitosamente"
    }


@router.get("/devices/readings/{student_id}")
def get_readings(
    student_id: str,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    db = get_dynamodb_resource()
    heart_table = db.Table("heart_rate_readings")

    response = heart_table.query(
        KeyConditionExpression="student_id = :sid",
        ExpressionAttributeValues={":sid": student_id},
        ScanIndexForward=False,
        Limit=limit
    )
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    return {"readings": items, "count": len(items), "student_id": student_id}


@router.put("/devices/{device_id}/toggle")
def toggle_device(
    device_id: str,
    user: dict = Depends(require_role(["Docentes"]))
):
    """Activa/desactiva un dispositivo (solo docentes)."""
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    response = devices_table.get_item(Key={"device_id": device_id})
    device = response.get("Item")

    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    new_status = not device.get("activo", True)

    devices_table.update_item(
        Key={"device_id": device_id},
        UpdateExpression="SET activo = :a",
        ExpressionAttributeValues={":a": new_status}
    )

    logger.info(
        "[DEVICE] Dispositivo %s %s por docente",
        device_id, "activado" if new_status else "desactivado"
    )

    return {
        "device_id": device_id,
        "activo": new_status,
        "mensaje": f"Dispositivo {'activado' if new_status else 'desactivado'} exitosamente"
    }


@router.get("/devices")
def list_devices(user: dict = Depends(require_role(["Docentes"]))):
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    response = devices_table.scan()
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    for item in items:
        item.pop("api_key", None)

    return {"devices": items, "count": len(items)}
