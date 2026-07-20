"""
Tests for the devices routes (register device, receive readings, list devices,
auto-register by MAC, MAC-based readings, toggle device).

Uses moto-mocked DynamoDB, mock auth tokens, and real API key verification flow.
"""

from datetime import datetime, timezone, timedelta
import secrets
import hashlib


class TestRegisterDevice:
    """POST /devices/register"""

    URL = "/devices/register"

    def test_register_device_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to register a device."""
        resp = client.post(
            self.URL,
            json={"student_id": "student-001", "nombre": "ESP32 Test"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "device_id" in data
        assert "api_key" in data
        assert data["student_id"] == "student-001"
        assert len(data["api_key"]) > 0

    def test_register_device_default_name(self, client, auth_header_teacher):
        """Without a nombre, the default 'ESP32 Cardiaco' should be used."""
        resp = client.post(
            self.URL,
            json={"student_id": "student-002"},
            headers=auth_header_teacher,
        )
        data = resp.json()
        assert data["nombre"] == "ESP32 Cardiaco"

    def test_register_device_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to register a device."""
        resp = client.post(
            self.URL,
            json={"student_id": "student-003"},
            headers=auth_header_student,
        )
        assert resp.status_code == 403

    def test_register_device_unauthorized(self, client):
        """Without auth, device registration should be unauthorized (401)."""
        resp = client.post(
            self.URL,
            json={"student_id": "student-004"},
        )
        assert resp.status_code == 401


class TestAutoRegisterDevice:
    """POST /devices/auto-register"""

    URL = "/devices/auto-register"

    def test_auto_register_new_device(self, client):
        """A new device should be auto-registered by MAC address."""
        resp = client.post(
            self.URL,
            json={
                "mac_address": "AA:BB:CC:DD:EE:01",
                "student_id": "student-mac-001",
                "nombre": "ESP32 Test MAC"
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "device_id" in data
        assert data["mac_address"] == "AA:BB:CC:DD:EE:01"
        assert data["student_id"] == "student-mac-001"
        assert data["activo"] is True

    def test_auto_register_existing_device_idempotent(self, client):
        """Registering the same MAC twice should return 200 both times (idempotent)."""
        mac = "AA:BB:CC:DD:EE:02"
        # First registration
        resp1 = client.post(
            self.URL,
            json={"mac_address": mac, "student_id": "student-mac-002"},
        )
        assert resp1.status_code == 200
        device_id_1 = resp1.json()["device_id"]

        # Second registration (same MAC)
        resp2 = client.post(
            self.URL,
            json={"mac_address": mac, "student_id": "student-mac-002"},
        )
        assert resp2.status_code == 200
        device_id_2 = resp2.json()["device_id"]

        # Should return the same device
        assert device_id_1 == device_id_2

    def test_auto_register_normalizes_mac_uppercase(self, client):
        """MAC address should be normalized to uppercase."""
        resp = client.post(
            self.URL,
            json={"mac_address": "aa:bb:cc:dd:ee:03", "student_id": "student-mac-003"},
        )
        assert resp.status_code == 200
        assert resp.json()["mac_address"] == "AA:BB:CC:DD:EE:03"

    def test_auto_register_invalid_mac_format(self, client):
        """An invalid MAC format should return 422."""
        resp = client.post(
            self.URL,
            json={"mac_address": "invalid-mac", "student_id": "student-mac-004"},
        )
        assert resp.status_code == 422

    def test_auto_register_missing_student_id(self, client):
        """Missing student_id should return 422."""
        resp = client.post(
            self.URL,
            json={"mac_address": "AA:BB:CC:DD:EE:05"},
        )
        assert resp.status_code == 422


class TestReceiveHeartRateReading:
    """POST /devices/reading"""

    READING_URL = "/devices/reading"
    REGISTER_URL = "/devices/register"

    def _register_device(self, client, headers):
        """Helper: register a device and return its API key."""
        resp = client.post(
            self.REGISTER_URL,
            json={"student_id": "hr-student-001"},
            headers=headers,
        )
        return resp.json()["api_key"]

    def test_receive_valid_reading(self, client, auth_header_teacher):
        """A valid heart rate reading should be recorded successfully."""
        api_key = self._register_device(client, auth_header_teacher)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": now},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bpm"] == 75
        assert data["student_id"] == "hr-student-001"
        assert "reading_id" in data

    def test_receive_reading_invalid_api_key(self, client):
        """An invalid API key should return 401."""
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": datetime.now(timezone.utc).isoformat()},
            headers={"X-Api-Key": "invalid-key"},
        )
        assert resp.status_code == 401

    def test_receive_reading_missing_auth(self, client):
        """No X-Api-Key and no X-Device-Mac should return 401."""
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        assert resp.status_code == 401

    def test_receive_reading_future_timestamp(self, client, auth_header_teacher):
        """A timestamp in the future should return 400."""
        api_key = self._register_device(client, auth_header_teacher)
        future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": future},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 400
        assert "futuro" in resp.json()["detail"].lower()

    def test_receive_reading_old_timestamp(self, client, auth_header_teacher):
        """A timestamp older than 24h should return 400."""
        api_key = self._register_device(client, auth_header_teacher)
        past = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": past},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 400
        assert "antiguo" in resp.json()["detail"].lower()

    def test_receive_reading_invalid_timestamp_format(self, client, auth_header_teacher):
        """A non-ISO timestamp should return 400."""
        api_key = self._register_device(client, auth_header_teacher)
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": "not-a-date"},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 400
        assert "inválido" in resp.json()["detail"].lower()

    def test_receive_reading_bpm_out_of_range(self, client, auth_header_teacher):
        """BPM outside 30-220 range should fail validation (422)."""
        api_key = self._register_device(client, auth_header_teacher)
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 250, "timestamp": now},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 422


class TestMacBasedReading:
    """POST /devices/reading con autenticación por MAC"""

    READING_URL = "/devices/reading"
    AUTO_REG_URL = "/devices/auto-register"

    def _auto_register(self, client, mac="AA:BB:CC:11:22:33", student_id="mac-reading-student"):
        """Helper: auto-register a device by MAC."""
        resp = client.post(
            self.AUTO_REG_URL,
            json={"mac_address": mac, "student_id": student_id},
        )
        return resp.json()

    def test_receive_reading_with_mac(self, client):
        """A registered MAC device should be able to send readings."""
        mac = "AA:BB:CC:11:22:33"
        self._auto_register(client, mac=mac)
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

    def test_api_key_still_works_after_mac_support(self, client, auth_header_teacher):
        """Backward compat: API key auth should still work for readings."""
        # Register device the old way
        resp = client.post(
            "/devices/register",
            json={"student_id": "legacy-student"},
            headers=auth_header_teacher,
        )
        api_key = resp.json()["api_key"]

        # Send reading with API key
        now = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            self.READING_URL,
            json={"bpm": 72, "timestamp": now},
            headers={"X-Api-Key": api_key},
        )
        assert resp.status_code == 200
        assert resp.json()["student_id"] == "legacy-student"


class TestToggleDevice:
    """PUT /devices/{device_id}/toggle"""

    AUTO_REG_URL = "/devices/auto-register"

    def _create_device(self, client):
        """Helper: create a device via auto-register and return device_id."""
        resp = client.post(
            self.AUTO_REG_URL,
            json={"mac_address": "AA:BB:CC:DD:EE:FF", "student_id": "toggle-student"},
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
    """GET /devices/readings/{student_id}"""

    READING_URL = "/devices/reading"
    REGISTER_URL = "/devices/register"
    GET_URL = "/devices/readings/hr-student-read"

    def _setup_reading(self, client):
        """Register device and insert a reading."""
        resp = client.post(
            self.REGISTER_URL,
            json={"student_id": "hr-student-read"},
            headers={"Authorization": "Bearer mock-teacher-token"},
        )
        api_key = resp.json()["api_key"]
        now = datetime.now(timezone.utc).isoformat()
        client.post(
            self.READING_URL,
            json={"bpm": 80, "timestamp": now},
            headers={"X-Api-Key": api_key},
        )
        return api_key

    def test_get_readings_authenticated(self, client):
        """An authenticated user should be able to get readings."""
        self._setup_reading(client)
        resp = client.get(
            self.GET_URL,
            headers={"Authorization": "Bearer mock-teacher-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == "hr-student-read"
        assert data["count"] >= 1
        assert len(data["readings"]) >= 1

    def test_get_readings_unauthorized(self, client):
        """Without auth, getting readings should be unauthorized (401)."""
        resp = client.get(self.GET_URL)
        assert resp.status_code == 401


class TestListDevices:
    """GET /devices"""

    REGISTER_URL = "/devices/register"
    LIST_URL = "/devices"

    def _register_device(self, client):
        client.post(
            self.REGISTER_URL,
            json={"student_id": "list-student"},
            headers={"Authorization": "Bearer mock-teacher-token"},
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
        """A student should NOT be able to list devices."""
        resp = client.get(self.LIST_URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_list_devices_unauthorized(self, client):
        """Without auth, listing devices should be unauthorized (401)."""
        resp = client.get(self.LIST_URL)
        assert resp.status_code == 401
