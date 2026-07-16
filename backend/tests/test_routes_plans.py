"""
Tests for the plans routes (create plan, get task status, download PDF).

Uses moto-mocked DynamoDB and mock auth tokens from conftest.py.
"""

import uuid


class TestCreatePlan:
    """POST /plan"""

    PLAN_URL = "/plan"

    def test_create_plan_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to create a plan."""
        payload = {
            "paciente_id": "pat-001",
            "tipo_plan": "Estandar",
            "alimentos": [
                {"nombre": "Arroz", "cantidad": "200g", "comida": "Almuerzo"},
            ],
        }
        resp = client.post(self.PLAN_URL, json=payload, headers=auth_header_teacher)
        assert resp.status_code == 202
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "PENDIENTE"
        assert "status_url" in data
        assert "ready_url" in data

    def test_create_plan_as_student(self, client, auth_header_student):
        """A student should also be able to create a plan."""
        payload = {
            "paciente_id": "pat-002",
            "tipo_plan": "Cetogenico",
        }
        resp = client.post(self.PLAN_URL, json=payload, headers=auth_header_student)
        assert resp.status_code == 202

    def test_create_plan_unauthorized(self, client):
        """Without auth, plan creation should be unauthorized (401)."""
        payload = {"paciente_id": "pat-003", "tipo_plan": "Estandar"}
        resp = client.post(self.PLAN_URL, json=payload)
        assert resp.status_code == 401

    def test_create_plan_empty_alimentos(self, client, auth_header_teacher):
        """Creating a plan without alimentos should still work."""
        payload = {"paciente_id": "pat-004", "tipo_plan": "Estandar"}
        resp = client.post(self.PLAN_URL, json=payload, headers=auth_header_teacher)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "PENDIENTE"


class TestGetTaskStatus:
    """GET /tasks/{task_id}"""

    def _create_task(self, client, headers):
        """Helper to create a plan and return its task_id."""
        payload = {"paciente_id": "pat-status", "tipo_plan": "Estandar"}
        resp = client.post("/plan", json=payload, headers=headers)
        return resp.json()["task_id"]

    def test_get_existing_task(self, client, auth_header_teacher):
        """Getting an existing task should return its data."""
        task_id = self._create_task(client, auth_header_teacher)
        resp = client.get(f"/tasks/{task_id}", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["estado_actual"] in ("PENDIENTE", "PROCESANDO", "COMPLETADO", "FALLIDO")
        assert data["paciente_id"] == "pat-status"

    def test_get_nonexistent_task(self, client, auth_header_teacher):
        """Getting a non-existent task should return 404."""
        resp = client.get(f"/tasks/{uuid.uuid4()}", headers=auth_header_teacher)
        assert resp.status_code == 404

    def test_get_task_unauthorized(self, client):
        """Without auth, task status should be unauthorized (401)."""
        resp = client.get(f"/tasks/{uuid.uuid4()}")
        assert resp.status_code == 401


class TestGetTaskReady:
    """GET /tasks/{task_id}/ready"""

    def _create_task(self, client, headers):
        payload = {"paciente_id": "pat-ready", "tipo_plan": "Estandar"}
        resp = client.post("/plan", json=payload, headers=headers)
        return resp.json()["task_id"]

    def test_ready_endpoint_existing(self, client, auth_header_teacher):
        """The ready endpoint should return status information."""
        task_id = self._create_task(client, auth_header_teacher)
        resp = client.get(f"/tasks/{task_id}/ready", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert "ready" in data
        assert "terminal" in data
        assert "should_continue_polling" in data

    def test_ready_nonexistent_task(self, client, auth_header_teacher):
        """Ready endpoint for non-existent task should return 404."""
        resp = client.get(f"/tasks/{uuid.uuid4()}/ready", headers=auth_header_teacher)
        assert resp.status_code == 404


class TestDownloadPlanPDF:
    """GET /plan/{task_id}/pdf"""

    def _create_task(self, client, headers):
        payload = {"paciente_id": "pat-pdf", "tipo_plan": "Estandar"}
        resp = client.post("/plan", json=payload, headers=headers)
        return resp.json()["task_id"]

    def test_download_pdf_existing_task(self, client, auth_header_teacher):
        """Downloading a PDF for an existing task should return a PDF."""
        task_id = self._create_task(client, auth_header_teacher)
        resp = client.get(f"/plan/{task_id}/pdf", headers=auth_header_teacher)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")

    def test_download_pdf_nonexistent_task(self, client, auth_header_teacher):
        """Downloading PDF for non-existent task should return 404."""
        resp = client.get(f"/plan/{uuid.uuid4()}/pdf", headers=auth_header_teacher)
        assert resp.status_code == 404
