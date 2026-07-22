"""
Tests for the devices routes (register device, receive readings, list devices).

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

    def test_receive_reading_missing_api_key(self, client):
        """A missing API key should return 422 (FastAPI validation)."""
        resp = client.post(
            self.READING_URL,
            json={"bpm": 75, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        assert resp.status_code == 422

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
