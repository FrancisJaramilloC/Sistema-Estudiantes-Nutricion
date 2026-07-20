"""
Tests for the devices routes (pairing code flow, receive readings, list devices,
auto-register by MAC + pairing code, MAC-based readings, toggle device).

Uses mocked DynamoDB, mock auth tokens, and real API key verification flow.
"""

from datetime import datetime, timezone, timedelta
import secrets
import hashlib

from app.database import get_dynamodb_resource


class TestPairingCode:
    """POST /devices/pairing-code (estudiante y docente)"""

    CREATE_URL = "/devices/pairing-code"

    def _seed_student(self, username):
        db = get_dynamodb_resource()
        db.Table("users_table").put_item(Item={
            "username": username,
            "nombre": "Alumno Prueba",
            "role": "Estudiantes",
        })

    def test_create_pairing_code_as_student(self, client, auth_header_student):
        """A student should be able to generate a pairing code for themselves."""
        resp = client.post(self.CREATE_URL, headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data and len(data["code"]) == 8
        assert data["student_id"] == "estudiante_prueba"
        assert data["ttl_seconds"] == 300

    def test_create_pairing_code_unauthorized(self, client):
        """Without auth, code generation should be 401."""
        resp = client.post(self.CREATE_URL)
        assert resp.status_code == 401

    def test_teacher_generates_code_for_registered_student(self, client, auth_header_teacher):
        """A teacher can generate a code linked to a specific registered student."""
        self._seed_student("alumno_001")
        resp = client.post(
            self.CREATE_URL,
            json={"student_id": "alumno_001"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == "alumno_001"

    def test_teacher_generates_code_for_unknown_student_fails(self, client, auth_header_teacher):
        """A teacher cannot generate a code for a non-registered student."""
        resp = client.post(
            self.CREATE_URL,
            json={"student_id": "no_existe_999"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 404

    def test_teacher_code_can_pair_device(self, client, auth_header_teacher):
        """A device using a teacher-generated code pairs to that student."""
        self._seed_student("alumno_002")
        code = client.post(
            self.CREATE_URL,
            json={"student_id": "alumno_002"},
            headers=auth_header_teacher,
        ).json()["code"]
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:77", "pairing_code": code},
        )
        assert resp.status_code == 200
        assert resp.json()["student_id"] == "alumno_002"

    def test_auto_register_with_valid_code(self, client, auth_header_student):
        """A valid, unused pairing code should register the device under the student."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:01", "pairing_code": code},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mac_address"] == "AA:BB:CC:DD:EE:01"
        assert data["student_id"] == "estudiante_prueba"
        assert data["activo"] is True

    def test_auto_register_reused_code_fails(self, client, auth_header_student):
        """Using the same code twice should fail the second time (single use)."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp1 = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:02", "pairing_code": code},
        )
        assert resp1.status_code == 200
        resp2 = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:03", "pairing_code": code},
        )
        assert resp2.status_code == 400
        assert "utilizado" in resp2.json()["detail"].lower()

    def test_auto_register_invalid_code_fails(self, client):
        """An unknown pairing code should return 404."""
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:04", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 404

    def test_auto_register_missing_code_fails(self, client):
        """Missing pairing_code should return 422."""
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:05"},
        )
        assert resp.status_code == 422

    def test_auto_register_invalid_mac_format(self, client):
        """An invalid MAC format should return 422."""
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "invalid-mac", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 422

    def test_reading_after_pairing_uses_student(self, client, auth_header_student):
        """A reading from a paired MAC resolves to the student who generated the code."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        mac = "AA:BB:CC:DD:EE:06"
        client.post("/devices/auto-register", json={"mac_address": mac, "pairing_code": code})
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            "/devices/reading",
            json={"bpm": 80, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 200
        assert resp.json()["student_id"] == "estudiante_prueba"
    """POST /devices/pairing-code y validación de auto-registro"""

    CREATE_URL = "/devices/pairing-code"
    AUTO_URL = "/devices/auto-register"

    def test_create_pairing_code_as_student(self, client, auth_header_student):
        """A student should be able to generate a pairing code."""
        resp = client.post(self.CREATE_URL, headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data and len(data["code"]) == 8
        assert data["ttl_seconds"] == 300

    def test_create_pairing_code_unauthorized(self, client):
        """Without auth, code generation should be 401."""
        resp = client.post(self.CREATE_URL)
        assert resp.status_code == 401

    def test_auto_register_with_valid_code(self, client, auth_header_student):
        """A valid, unused pairing code should register the device under the student."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp = client.post(
            self.AUTO_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:01", "pairing_code": code},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mac_address"] == "AA:BB:CC:DD:EE:01"
        assert data["student_id"] == "estudiante_prueba"
        assert data["activo"] is True

    def test_auto_register_reused_code_fails(self, client, auth_header_student):
        """Using the same code twice should fail the second time (single use)."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp1 = client.post(
            self.AUTO_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:02", "pairing_code": code},
        )
        assert resp1.status_code == 200
        resp2 = client.post(
            self.AUTO_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:03", "pairing_code": code},
        )
        assert resp2.status_code == 400
        assert "utilizado" in resp2.json()["detail"].lower()

    def test_auto_register_invalid_code_fails(self, client):
        """An unknown pairing code should return 404."""
        resp = client.post(
            self.AUTO_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:04", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 404

    def test_auto_register_missing_code_fails(self, client):
        """Missing pairing_code should return 422."""
        resp = client.post(
            self.AUTO_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:05"},
        )
        assert resp.status_code == 422

    def test_auto_register_invalid_mac_format(self, client):
        """An invalid MAC format should return 422."""
        resp = client.post(
            self.AUTO_URL,
            json={"mac_address": "invalid-mac", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 422

    def test_reading_after_pairing_uses_student(self, client, auth_header_student):
        """A reading from a paired MAC resolves to the student who generated the code."""
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        mac = "AA:BB:CC:DD:EE:06"
        client.post(self.AUTO_URL, json={"mac_address": mac, "pairing_code": code})
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            "/devices/reading",
            json={"bpm": 80, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 200
        assert resp.json()["student_id"] == "estudiante_prueba"


class TestAutoRegisterDevice:
    """POST /devices/auto-register (idempotencia por MAC)"""

    URL = "/devices/auto-register"

    def _pair(self, client, mac):
        """Helper: genera código de estudiante y auto-registra la MAC dada."""
        code = client.post(
            "/devices/pairing-code",
            headers={"Authorization": "Bearer mock-student-token"},
        ).json()["code"]
        return client.post(self.URL, json={"mac_address": mac, "pairing_code": code})

    def test_auto_register_existing_device_idempotent(self, client):
        """Registering the same MAC twice should return 200 both times (idempotent)."""
        mac = "AA:BB:CC:DD:EE:02"
        resp1 = self._pair(client, mac)
        assert resp1.status_code == 200
        device_id_1 = resp1.json()["device_id"]

        resp2 = client.post(
            self.URL,
            json={"mac_address": mac, "pairing_code": "ZZZZZZZZ"},
        )
        assert resp2.status_code == 200
        device_id_2 = resp2.json()["device_id"]
        assert device_id_1 == device_id_2

    def test_auto_register_normalizes_mac_uppercase(self, client):
        """MAC address should be normalized to uppercase."""
        resp = self._pair(client, "aa:bb:cc:dd:ee:03")
        assert resp.status_code == 200
        assert resp.json()["mac_address"] == "AA:BB:CC:DD:EE:03"


class TestReceiveHeartRateReading:
    """POST /devices/reading (autenticación por MAC vía código de emparejamiento)"""

    READING_URL = "/devices/reading"
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def _pair(self, client, mac, student_token="mock-teacher-token", student_id="hr-student-001"):
        """Helper: genera código y auto-registra la MAC dada."""
        if student_token == "mock-student-token":
            code = client.post(
                self.PAIRING_URL,
                headers={"Authorization": "Bearer mock-student-token"},
            ).json()["code"]
        else:
            get_dynamodb_resource().Table("users_table").put_item(
                Item={"username": student_id, "nombre": student_id, "role": "Estudiantes"}
            )
            code = client.post(
                self.PAIRING_URL,
                json={"student_id": student_id},
                headers={"Authorization": "Bearer mock-teacher-token"},
            ).json()["code"]
        client.post(
            self.AUTO_REG_URL,
            json={"mac_address": mac, "pairing_code": code},
        )
        return student_id

    def test_receive_valid_reading(self, client):
        """A valid heart rate reading should be recorded successfully."""
        mac = "AA:BB:CC:21:22:33"
        self._pair(client, mac)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bpm"] == 75
        assert data["student_id"] == "hr-student-001"
        assert "reading_id" in data

    def test_receive_reading_missing_auth(self, client):
        """No X-Device-Mac should return 401."""
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        assert resp.status_code == 401

    def test_receive_reading_future_timestamp(self, client):
        """A timestamp in the future should return 400."""
        mac = "AA:BB:CC:21:22:34"
        self._pair(client, mac)
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": future},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 400
        assert "futuro" in resp.json()["detail"].lower()

    def test_receive_reading_old_timestamp(self, client):
        """A timestamp older than 24h should return 400."""
        mac = "AA:BB:CC:21:22:35"
        self._pair(client, mac)
        past = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": past},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 400
        assert "antiguo" in resp.json()["detail"].lower()

    def test_receive_reading_invalid_timestamp_format(self, client):
        """A non-ISO timestamp should return 400."""
        mac = "AA:BB:CC:21:22:36"
        self._pair(client, mac)
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": "not-a-date"},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 400
        assert "inválido" in resp.json()["detail"].lower()

    def test_receive_reading_bpm_out_of_range(self, client):
        """BPM outside 30-220 range should fail validation (422)."""
        mac = "AA:BB:CC:21:22:37"
        self._pair(client, mac)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 250, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 422


class TestMacBasedReading:
    """POST /devices/reading con autenticación por MAC"""

    READING_URL = "/devices/reading"
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def _auto_register(self, client, mac="AA:BB:CC:11:22:33", teacher_token="mock-teacher-token", student_id="mac-reading-student"):
        """Helper: auto-register a device by MAC using a generated pairing code."""
        if teacher_token == "mock-teacher-token":
            client.post(
                "/devices/pairing-code",
                json={"student_id": student_id},
                headers={"Authorization": "Bearer mock-teacher-token"},
            )
        else:
            client.post(
                "/devices/pairing-code",
                headers={"Authorization": "Bearer mock-student-token"},
            )
        # ensure student exists
        get_dynamodb_resource().Table("users_table").put_item(
            Item={"username": student_id, "nombre": student_id, "role": "Estudiantes"}
        )
        code = client.post(
            self.PAIRING_URL,
            json={"student_id": student_id} if teacher_token == "mock-teacher-token" else None,
            headers={"Authorization": f"Bearer {teacher_token}"},
        ).json()["code"]
        resp = client.post(
            self.AUTO_REG_URL,
            json={"mac_address": mac, "pairing_code": code},
        )
        return resp.json()

    def test_receive_reading_with_mac(self, client):
        """A registered MAC device should be able to send readings."""
        mac = "AA:BB:CC:11:22:33"
        self._auto_register(client, mac)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 80, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bpm"] == 80
        assert data["student_id"] == "mac-reading-student"

    def test_receive_reading_invalid_mac(self, client):
        """An unregistered MAC should return 401."""
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 80, "timestamp": now},
            headers={"X-Device-Mac": "FF:FF:FF:FF:FF:FF"},
        )
        assert resp.status_code == 401

    def test_receive_reading_no_auth_at_all(self, client):
        """No auth headers at all should return 401."""
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 80, "timestamp": now},
        )
        assert resp.status_code == 401


class TestToggleDevice:
    """PUT /devices/{device_id}/toggle"""

    AUTO_REG_URL = "/devices/auto-register"
    PAIRING_URL = "/devices/pairing-code"

    def _create_device(self, client):
        """Helper: create a device via auto-register (pairing code) and return device_id."""
        code = client.post(
            self.PAIRING_URL,
            headers={"Authorization": "Bearer mock-teacher-token"},
        ).json()["code"]
        resp = client.post(
            self.AUTO_REG_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:FF", "pairing_code": code},
        )
        return resp.json()["device_id"]

    def test_toggle_device_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to toggle a device's active status."""
        device_id = self._create_device(client)

        # Toggle off
        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["activo"] is False

        # Toggle on
        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["activo"] is True

    def test_toggle_device_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to toggle a device."""
        device_id = self._create_device(client)
        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_student,
        )
        assert resp.status_code == 403

    def test_toggle_nonexistent_device(self, client, auth_header_teacher):
        """Toggling a nonexistent device should return 404."""
        resp = client.put(
            "/devices/nonexistent-device-id/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 404


class TestGetReadings:
    """GET /devices/readings/{device_id}"""

    READING_URL = "/devices/reading"
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def _setup_reading(self, client):
        """Pair device and insert a reading, return device_id."""
        get_dynamodb_resource().Table("users_table").put_item(
            Item={"username": "hr-student-read", "nombre": "hr-student-read", "role": "Estudiantes"}
        )
        code = client.post(
            self.PAIRING_URL,
            json={"student_id": "hr-student-read"},
            headers={"Authorization": "Bearer mock-teacher-token"},
        ).json()["code"]
        mac = "AA:BB:CC:99:88:77"
        resp = client.post(
            self.AUTO_REG_URL,
            json={"mac_address": mac, "pairing_code": code},
        )
        device_id = resp.json()["device_id"]
        now = datetime.now(timezone.utc).isoformat()
        client.post(
            self.READING_URL,
            json={"bpm": 80, "timestamp": now},
            headers={"X-Device-Mac": mac},
        )
        return device_id

    def test_get_readings_authenticated(self, client):
        """An authenticated user should be able to get readings by device_id."""
        device_id = self._setup_reading(client)
        resp = client.get(
            f"/devices/readings/{device_id}",
            headers={"Authorization": "Bearer mock-teacher-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_id"] == device_id
        assert data["count"] >= 1
        assert len(data["readings"]) >= 1

    def test_get_readings_unauthorized(self, client):
        """Without auth, getting readings should be unauthorized (401)."""
        resp = client.get("/devices/readings/some-device-id")
        assert resp.status_code == 401


class TestListDevices:
    """GET /devices"""

    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"
    LIST_URL = "/devices"

    def _register_device(self, client):
        code = client.post(
            self.PAIRING_URL,
            headers={"Authorization": "Bearer mock-teacher-token"},
        ).json()["code"]
        client.post(
            self.AUTO_REG_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:AB", "pairing_code": code},
        )

    def test_list_devices_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to list all devices."""
        self._register_device(client)
        resp = client.get(self.LIST_URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert len(data["devices"]) >= 1
        # API keys should not be exposed
        for device in data["devices"]:
            assert "api_key" not in device

    def test_list_devices_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to list all devices."""
        resp = client.get(self.LIST_URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_list_devices_unauthorized(self, client):
        """Without auth, listing devices should be unauthorized (401)."""
        resp = client.get(self.LIST_URL)
        assert resp.status_code == 401


class TestListMyDevices:
    """GET /devices/my-devices"""

    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def test_list_my_devices_as_student(self, client, auth_header_student):
        """A student should be able to list their own devices."""
        code = client.post(
            self.PAIRING_URL,
            headers=auth_header_student,
        ).json()["code"]
        client.post(
            self.AUTO_REG_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:01", "pairing_code": code},
        )
        resp = client.get("/devices/my-devices", headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert len(data["devices"]) >= 1
        # All devices should belong to the student
        for device in data["devices"]:
            assert device["student_id"] == "estudiante_prueba"
            assert "api_key" not in device

    def test_list_my_devices_as_teacher(self, client, auth_header_teacher):
        """A teacher should get empty list (no devices linked to teacher account)."""
        resp = client.get("/devices/my-devices", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_list_my_devices_unauthorized(self, client):
        """Without auth, listing my devices should be unauthorized (401)."""
        resp = client.get("/devices/my-devices")
        assert resp.status_code == 401
