from datetime import datetime, timezone, timedelta

from app.database import get_dynamodb_resource


class TestPairingCode:
    CREATE_URL = "/devices/pairing-code"

    def _seed_student(self, username):
        db = get_dynamodb_resource()
        db.Table("users_table").put_item(Item={
            "username": username,
            "nombre": "Alumno Prueba",
            "role": "Estudiantes",
        })

    def test_create_pairing_code_as_student(self, client, auth_header_student):
        resp = client.post(self.CREATE_URL, headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data and len(data["code"]) == 8
        assert data["student_id"] == "estudiante_prueba"
        assert data["ttl_seconds"] == 300

    def test_create_pairing_code_unauthorized(self, client):
        resp = client.post(self.CREATE_URL)
        assert resp.status_code == 401

    def test_teacher_generates_code_for_registered_student(self, client, auth_header_teacher):
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
        resp = client.post(
            self.CREATE_URL,
            json={"student_id": "no_existe_999"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 404

    def test_teacher_code_can_pair_device(self, client, auth_header_teacher):
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
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:04", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 404

    def test_auto_register_missing_code_fails(self, client):
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:05"},
        )
        assert resp.status_code == 422

    def test_auto_register_invalid_mac_format(self, client):
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "invalid-mac", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp.status_code == 422

    def test_auto_register_returns_mqtt_credentials(self, client, auth_header_student):
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:42", "pairing_code": code},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "mqtt_broker" in data
        assert "mqtt_username" in data
        assert "mqtt_password" in data
        assert data["mqtt_username"] == "AA:BB:CC:DD:EE:42"
        assert len(data["mqtt_password"]) == 24

    def test_auto_register_idempotent_returns_mqtt_credentials(self, client, auth_header_student):
        code = client.post(self.CREATE_URL, headers=auth_header_student).json()["code"]
        resp1 = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:99", "pairing_code": code},
        )
        device_id = resp1.json()["device_id"]

        resp2 = client.post(
            "/devices/auto-register",
            json={"mac_address": "AA:BB:CC:DD:EE:99", "pairing_code": "ZZZZZZZZ"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["device_id"] == device_id
        assert "mqtt_broker" in resp2.json()


class TestAutoRegisterDevice:
    URL = "/devices/auto-register"

    def _pair(self, client, mac):
        code = client.post(
            "/devices/pairing-code",
            headers={"Authorization": "Bearer mock-student-token"},
        ).json()["code"]
        return client.post(self.URL, json={"mac_address": mac, "pairing_code": code})

    def test_auto_register_existing_device_idempotent(self, client):
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
        resp = self._pair(client, "aa:bb:cc:dd:ee:03")
        assert resp.status_code == 200
        assert resp.json()["mac_address"] == "AA:BB:CC:DD:EE:03"


class TestToggleDevice:
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def _create_device(self, client):
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
        device_id = self._create_device(client)

        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["activo"] is False

        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["activo"] is True

    def test_toggle_device_as_student_forbidden(self, client, auth_header_student):
        device_id = self._create_device(client)
        resp = client.put(
            f"/devices/{device_id}/toggle",
            headers=auth_header_student,
        )
        assert resp.status_code == 403

    def test_toggle_nonexistent_device(self, client, auth_header_teacher):
        resp = client.put(
            "/devices/nonexistent-device-id/toggle",
            headers=auth_header_teacher,
        )
        assert resp.status_code == 404


class TestGetReadings:
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def _setup_reading(self, client):
        db = get_dynamodb_resource()
        db.Table("users_table").put_item(
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

        db.Table("heart_rate_readings").put_item(Item={
            "device_id": device_id,
            "timestamp": now,
            "reading_id": "test-reading-001",
            "student_id": "hr-student-read",
            "bpm": 80,
            "created_at": now,
        })
        return device_id

    def test_get_readings_authenticated(self, client):
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
        resp = client.get("/devices/readings/some-device-id")
        assert resp.status_code == 401


class TestListDevices:
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
        self._register_device(client)
        resp = client.get(self.LIST_URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert len(data["devices"]) >= 1
        for device in data["devices"]:
            assert "api_key" not in device

    def test_list_devices_as_student_forbidden(self, client, auth_header_student):
        resp = client.get(self.LIST_URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_list_devices_unauthorized(self, client):
        resp = client.get(self.LIST_URL)
        assert resp.status_code == 401


class TestListMyDevices:
    PAIRING_URL = "/devices/pairing-code"
    AUTO_REG_URL = "/devices/auto-register"

    def test_list_my_devices_as_student(self, client, auth_header_student):
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
        for device in data["devices"]:
            assert device["student_id"] == "estudiante_prueba"
            assert "api_key" not in device

    def test_list_my_devices_as_teacher(self, client, auth_header_teacher):
        resp = client.get("/devices/my-devices", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_list_my_devices_unauthorized(self, client):
        resp = client.get("/devices/my-devices")
        assert resp.status_code == 401
