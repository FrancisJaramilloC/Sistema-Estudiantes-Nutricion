import json
import logging
import secrets
import string
import threading
import time
import uuid
from datetime import datetime, timezone

import docker
import paho.mqtt.client as mqtt

from app.config import MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC_PREFIX, MQTT_PASSWD_FILE, MOSQUITTO_CONTAINER
from app.database import get_dynamodb_resource

logger = logging.getLogger("nutria.mqtt")

_mqtt_client = None
_docker_client = None


def _get_docker():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
    return _docker_client


def get_mqtt_client():
    global _mqtt_client
    return _mqtt_client


def _on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("[MQTT] Conectado al broker %s:%d", MQTT_HOST, MQTT_PORT)
        topic = f"{MQTT_TOPIC_PREFIX}/+/lecturas"
        client.subscribe(topic, qos=1)
        logger.info("[MQTT] Suscrito a %s", topic)
    else:
        logger.error("[MQTT] Error de conexión: código %d", rc)


def _on_message(client, userdata, msg):
    try:
        mac = _extract_mac_from_topic(msg.topic)
        if not mac:
            return

        payload = json.loads(msg.payload.decode())
        bpm = payload.get("bpm")
        timestamp = payload.get("timestamp")

        if not bpm or not timestamp:
            logger.warning("[MQTT] Mensaje inválido desde %s: faltan campos", mac)
            return

        db = get_dynamodb_resource()
        devices_table = db.Table("devices")
        heart_table = db.Table("heart_rate_readings")

        device = _find_device_by_mac(devices_table, mac)
        if not device:
            logger.warning("[MQTT] Dispositivo no registrado: %s", mac)
            return
        if not device.get("activo", True):
            logger.warning("[MQTT] Dispositivo desactivado: %s", mac)
            return

        try:
            ts = datetime.fromisoformat(timestamp)
            ts_now = datetime.now(timezone.utc)
            if ts > ts_now:
                logger.warning("[MQTT] Timestamp futuro desde %s", mac)
                return
            diff_hours = abs((ts_now - ts).total_seconds()) / 3600
            if diff_hours > 24:
                logger.warning("[MQTT] Timestamp muy antiguo desde %s", mac)
                return
        except ValueError:
            logger.warning("[MQTT] Timestamp inválido desde %s: %s", mac, timestamp)
            return

        reading_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        heart_table.put_item(Item={
            "device_id": device["device_id"],
            "timestamp": timestamp,
            "reading_id": reading_id,
            "student_id": device["student_id"],
            "bpm": bpm,
            "created_at": now
        })

        logger.info(
            "[MQTT_HEART_RATE] Lectura registrada: device=%s, student=%s, bpm=%d",
            device["device_id"], device["student_id"], bpm
        )

        from app.sse_handler import broadcast as sse_broadcast
        try:
            loop = None
            try:
                import asyncio
                loop = asyncio.get_event_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                loop.create_task(sse_broadcast(device["device_id"], {
                    "reading_id": reading_id,
                    "device_id": device["device_id"],
                    "student_id": device["student_id"],
                    "bpm": bpm,
                    "timestamp": timestamp,
                    "created_at": now,
                }))
        except Exception as sse_err:
            logger.warning("[MQTT] Error broadcasting SSE: %s", sse_err)
    except Exception as e:
        logger.error("[MQTT] Error procesando mensaje: %s", e)


def _extract_mac_from_topic(topic: str) -> str:
    parts = topic.split("/")
    if len(parts) >= 2 and parts[0] == MQTT_TOPIC_PREFIX:
        return parts[1].upper()
    return None


def _find_device_by_mac(devices_table, mac_address: str):
    response = devices_table.scan(
        FilterExpression="mac_address = :m",
        ExpressionAttributeValues={":m": mac_address}
    )
    items = response.get("Items", [])
    return items[0] if items else None


def start_mqtt_client():
    global _mqtt_client
    if _mqtt_client is not None:
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect_async(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    _mqtt_client = client
    logger.info("[MQTT] Cliente iniciado (conexión asíncrona a %s:%d)", MQTT_HOST, MQTT_PORT)


def stop_mqtt_client():
    global _mqtt_client
    if _mqtt_client is not None:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        _mqtt_client = None
        logger.info("[MQTT] Cliente detenido")


def generate_mqtt_password() -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(24))


def sync_device_to_mosquitto(mac_address: str, password: str):
    mac = mac_address.upper().replace(":", "")
    try:
        container = _get_docker().containers.get(MOSQUITTO_CONTAINER)
        MOSQUITTO_INTERNAL_PASSWD_FILE = "/mosquitto/data/passwd"
        exit_code, output = container.exec_run(
            ["mosquitto_passwd", "-b", MOSQUITTO_INTERNAL_PASSWD_FILE, mac, password]
        )
        if exit_code == 0:
            logger.info("[MQTT_PASSWD] Credencial agregada para %s", mac)
            _reload_mosquitto()
        else:
            logger.error("[MQTT_PASSWD] Error agregando credencial para %s: %s", mac, output.decode())
    except Exception as e:
        logger.warning("[MQTT_PASSWD] Error agregando credencial para %s: %s", mac, e)


def _reload_mosquitto():
    try:
        container = _get_docker().containers.get(MOSQUITTO_CONTAINER)
        container.kill(signal="HUP")
        logger.info("[MQTT] Mosquitto recargado (SIGHUP via socket)")
    except Exception as e:
        logger.warning("[MQTT] No se pudo recargar Mosquitto: %s", e)


def sync_all_devices_to_mosquitto():
    try:
        db = get_dynamodb_resource()
        devices_table = db.Table("devices")
        response = devices_table.scan()
        devices = response.get("Items", [])

        for device in devices:
            mac = device.get("mac_address")
            mqtt_pass = device.get("mqtt_password")
            if mac and mqtt_pass:
                sync_device_to_mosquitto(mac, mqtt_pass)

        _reload_mosquitto()
        logger.info("[MQTT] Sincronización completa: %d dispositivos", len(devices))
    except Exception as e:
        logger.error("[MQTT] Error en sync_all_devices: %s", e)
