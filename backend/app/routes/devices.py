import uuid
import hashlib
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


class DeviceRegisterRequest(BaseModel):
    student_id: str
    nombre: str = Field(default="ESP32 Cardiaco")


class DeviceRegisterResponse(BaseModel):
    device_id: str
    api_key: str
    student_id: str
    nombre: str
    mensaje: str


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


def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(x_api_key: str = Header(..., alias="X-Api-Key")):
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


@router.post("/devices/register", response_model=DeviceRegisterResponse)
def register_device(
    req: DeviceRegisterRequest,
    user: dict = Depends(require_role(["Docentes"]))
):
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
        "created_at": now
    })

    logger.info(
        "[DEVICE] Dispositivo registrado: %s (estudiante: %s)",
        device_id, req.student_id
    )

    return DeviceRegisterResponse(
        device_id=device_id,
        api_key=api_key,
        student_id=req.student_id,
        nombre=req.nombre or "ESP32 Cardiaco",
        mensaje="Dispositivo registrado exitosamente. Guarda esta API Key, no se mostrará de nuevo."
    )


@router.post("/devices/reading")
def receive_reading(
    reading: HeartRateReading,
    device: dict = Depends(verify_api_key)
):
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
