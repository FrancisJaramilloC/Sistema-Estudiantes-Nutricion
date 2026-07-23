import uuid
import re
import secrets
import logging
import string
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.database import get_dynamodb_resource, convert_decimals
from app.auth import get_current_user, require_role
from app.mqtt_handler import generate_mqtt_password, sync_device_to_mosquitto, get_mqtt_client

logger = logging.getLogger("nutria.monitoring")
router = APIRouter(tags=["devices"])


class PairingCodeRequest(BaseModel):
    student_id: Optional[str] = Field(
        default=None,
        description="Solo para docentes: username del estudiante para quien se genera el código."
    )


class PairingCodeResponse(BaseModel):
    code: str
    student_id: str
    expires_at: str
    ttl_seconds: int
    mensaje: str


class DeviceAutoRegisterRequest(BaseModel):
    mac_address: str = Field(
        ...,
        pattern=r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$',
        description="Dirección MAC del dispositivo (formato XX:XX:XX:XX:XX:XX)"
    )
    pairing_code: str = Field(
        ...,
        min_length=6,
        max_length=16,
        description="Código temporal de emparejamiento"
    )
    nombre: str = Field(default="ESP32 Cardiaco")


def _normalize_mac(mac: str) -> str:
    return mac.upper().strip()


def _find_device_by_mac(devices_table, mac_address: str):
    response = devices_table.scan(
        FilterExpression="mac_address = :m",
        ExpressionAttributeValues={":m": mac_address}
    )
    items = response.get("Items", [])
    return items[0] if items else None


@router.post("/devices/pairing-code", response_model=PairingCodeResponse)
def create_pairing_code(
    req: PairingCodeRequest = PairingCodeRequest(),
    user: dict = Depends(require_role(["Estudiantes", "Docentes"]))
):
    db = get_dynamodb_resource()
    users_table = db.Table("users_table")
    pairing_table = db.Table("pairing_codes")

    groups = user.get("cognito:groups", ["Estudiantes"])
    is_teacher = "Docentes" in groups

    if is_teacher and req.student_id:
        student_id = req.student_id.strip()
        existing = users_table.get_item(Key={"username": student_id}).get("Item")
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"El estudiante '{student_id}' no está registrado en el sistema."
            )
    else:
        student_id = user.get("username")

    if not student_id:
        raise HTTPException(status_code=400, detail="No se pudo identificar al estudiante")

    ttl_seconds = 300
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(8))

    pairing_table.put_item(Item={
        "code": code,
        "student_id": student_id,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_at_ttl": int(expires_at.timestamp()),
        "used": False
    })

    logger.info(
        "[PAIRING] Código de emparejamiento generado para estudiante: %s",
        student_id
    )

    return PairingCodeResponse(
        code=code,
        student_id=student_id,
        expires_at=expires_at.isoformat(),
        ttl_seconds=ttl_seconds,
        mensaje="Usa este código en el portal del ESP32. Expira en 5 minutos y es de un solo uso."
    )


@router.post("/devices/auto-register")
def auto_register_device(req: DeviceAutoRegisterRequest):
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    mac = _normalize_mac(req.mac_address)

    existing = _find_device_by_mac(devices_table, mac)
    if existing:
        logger.info(
            "[DEVICE] Dispositivo ya registrado por MAC: %s (estudiante: %s)",
            existing["device_id"], existing["student_id"]
        )
        from app.config import MQTT_EXTERNAL_HOST, MQTT_PORT

        mqtt_password = existing.get("mqtt_password", "")
        if not mqtt_password:
            mqtt_password = generate_mqtt_password()
            devices_table.update_item(
                Key={"device_id": existing["device_id"]},
                UpdateExpression="SET mqtt_password = :p",
                ExpressionAttributeValues={":p": mqtt_password}
            )

        sync_device_to_mosquitto(mac, mqtt_password)

        return {
            "device_id": existing["device_id"],
            "mac_address": mac,
            "student_id": existing["student_id"],
            "nombre": existing.get("nombre", "ESP32 Cardiaco"),
            "activo": existing.get("activo", True),
            "mqtt_broker": f"{MQTT_EXTERNAL_HOST}:{MQTT_PORT}",
            "mqtt_username": mac.replace(":", ""),
            "mqtt_password": mqtt_password,
            "mensaje": "Dispositivo ya estaba registrado."
        }

    pairing_table = db.Table("pairing_codes")
    response = pairing_table.get_item(Key={"code": req.pairing_code})
    pairing = response.get("Item")

    if not pairing:
        raise HTTPException(
            status_code=404,
            detail="Código de emparejamiento inválido o inexistente."
        )
    if pairing.get("used", False):
        raise HTTPException(
            status_code=400,
            detail="El código de emparejamiento ya fue utilizado."
        )

    expires_at = datetime.fromisoformat(pairing["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="El código de emparejamiento ha expirado."
        )

    student_id = pairing["student_id"]

    pairing_table.update_item(
        Key={"code": req.pairing_code},
        UpdateExpression="SET used = :u",
        ExpressionAttributeValues={":u": True}
    )

    device_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    mqtt_password = generate_mqtt_password()

    from app.config import MQTT_HOST, MQTT_PORT, MQTT_EXTERNAL_HOST

    devices_table.put_item(Item={
        "device_id": device_id,
        "mac_address": mac,
        "student_id": student_id,
        "nombre": req.nombre or "ESP32 Cardiaco",
        "activo": True,
        "auth_type": "mac",
        "mqtt_password": mqtt_password,
        "mqtt_broker_host": MQTT_HOST,
        "mqtt_broker_port": MQTT_PORT,
        "created_at": now
    })

    sync_device_to_mosquitto(mac, mqtt_password)

    logger.info(
        "[DEVICE] Dispositivo auto-registrado por MAC: %s (MAC: %s, estudiante: %s)",
        device_id, mac, student_id
    )

    return {
        "device_id": device_id,
        "mac_address": mac,
        "student_id": student_id,
        "nombre": req.nombre or "ESP32 Cardiaco",
        "activo": True,
        "mqtt_broker": f"{MQTT_EXTERNAL_HOST}:{MQTT_PORT}",
        "mqtt_username": mac.replace(":", ""),
        "mqtt_password": mqtt_password,
        "mensaje": "Dispositivo registrado exitosamente."
    }


@router.get("/devices/readings/{device_id}")
def get_readings(
    device_id: str,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    db = get_dynamodb_resource()
    heart_table = db.Table("heart_rate_readings")

    response = heart_table.query(
        KeyConditionExpression="device_id = :did",
        ExpressionAttributeValues={":did": device_id},
        ScanIndexForward=False,
        Limit=limit
    )
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    return {"readings": items, "count": len(items), "device_id": device_id}


@router.put("/devices/{device_id}/toggle")
def toggle_device(
    device_id: str,
    user: dict = Depends(require_role(["Docentes"]))
):
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


@router.get("/devices/my-devices")
def list_my_devices(user: dict = Depends(get_current_user)):
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    student_id = user.get("username")

    response = devices_table.scan(
        FilterExpression="student_id = :sid",
        ExpressionAttributeValues={":sid": student_id}
    )
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    for item in items:
        item.pop("api_key", None)

    return {"devices": items, "count": len(items)}


@router.post("/devices/{device_id}/unpair")
def unpair_device(
    device_id: str,
    user: dict = Depends(require_role(["Docentes", "Estudiantes"]))
):
    db = get_dynamodb_resource()
    devices_table = db.Table("devices")

    response = devices_table.get_item(Key={"device_id": device_id})
    device = response.get("Item")

    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    groups = user.get("cognito:groups", ["Estudiantes"])
    is_teacher = "Docentes" in groups
    student_id = user.get("username")

    if not is_teacher and device.get("student_id") != student_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para desvincular este dispositivo")

    mac = device.get("mac_address", "")
    new_password = generate_mqtt_password()

    devices_table.update_item(
        Key={"device_id": device_id},
        UpdateExpression="SET mqtt_password = :p, activo = :a",
        ExpressionAttributeValues={":p": new_password, ":a": False}
    )

    from app.mqtt_handler import sync_device_to_mosquitto
    if mac:
        sync_device_to_mosquitto(mac, new_password)

    mqtt = get_mqtt_client()
    if mqtt and mac:
        from app.config import MQTT_TOPIC_PREFIX
        import json as j
        cmd_topic = f"{MQTT_TOPIC_PREFIX}/{mac.replace(':', '').upper()}/comandos"
        mqtt.publish(cmd_topic, j.dumps({"comando": "reset", "motivo": "desvinculado"}), qos=1)

    logger.info("[DEVICE] Dispositivo %s desvinculado por %s", device_id, student_id)

    return {
        "mensaje": "Dispositivo desvinculado. El ESP32 se reiniciará en modo configuración.",
        "device_id": device_id
    }
