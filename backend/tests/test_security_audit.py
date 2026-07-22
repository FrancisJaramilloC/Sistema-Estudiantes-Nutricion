"""
Tests for auth security fix: public registration forces Estudiantes role (RF - Seguridad).
Also tests admin create-user endpoint.
"""
import uuid


class TestRegisterSecurity:
    """POST /auth/register - public registration forces Estudiantes role."""

    URL = "/auth/register"

    def _get_fake_users_table(self):
        from tests.conftest import _get_fake_table
        return _get_fake_table("users_table")

    def test_registro_estudiante(self, client):
        resp = client.post(self.URL, json={
            "username": f"est-test-{uuid.uuid4().hex[:8]}",
            "email": f"est@test.com",
            "password": "Test1234!",
            "role": "Estudiantes",
            "nombre": "Test Student",
            "cedula": f"17{uuid.uuid4().hex[:8]}",
            "fecha_nacimiento": "2000-01-01",
        })
        assert resp.status_code == 201

    def test_registro_docente_forzado_a_estudiante(self, client):
        """Public registration with role=Docentes must be forced to Estudiantes."""
        username = f"test-docente-{uuid.uuid4().hex[:8]}"
        resp = client.post(self.URL, json={
            "username": username,
            "email": f"docente@test.com",
            "password": "Test1234!",
            "role": "Docentes",
            "nombre": "Intento Docente",
            "cedula": f"17{uuid.uuid4().hex[:8]}",
            "fecha_nacimiento": "1990-05-15",
        })
        assert resp.status_code == 201
        # Verify stored role is Estudiantes
        table = self._get_fake_users_table()
        stored = table.get_item(Key={"username": username})
        assert stored.get("Item", {}).get("role") == "Estudiantes"


class TestAdminCreateUser:
    """POST /admin/create-user"""

    URL = "/admin/create-user"

    def test_create_user_unauthorized(self, client):
        resp = client.post(self.URL, json={
            "username": "test-user",
            "email": "test@test.com",
            "password": "Test1234!",
            "role": "Estudiantes",
            "nombre": "Test",
            "cedula": "12345",
            "fecha_nacimiento": "2000-01-01",
        })
        assert resp.status_code == 401

    def test_create_user_student_forbidden_for_students(self, client, auth_header_student):
        resp = client.post(self.URL, json={
            "username": "test-user",
            "email": "test@test.com",
            "password": "Test1234!",
            "role": "Estudiantes",
            "nombre": "Test",
            "cedula": "12345",
            "fecha_nacimiento": "2000-01-01",
        }, headers=auth_header_student)
        assert resp.status_code == 403

    def test_create_user_as_teacher(self, client, auth_header_teacher):
        username = f"admin-created-{uuid.uuid4().hex[:8]}"
        resp = client.post(self.URL, json={
            "username": username,
            "email": f"admincreated@test.com",
            "password": "Test1234!",
            "role": "Docentes",
            "nombre": "Admin Created",
            "cedula": f"17{uuid.uuid4().hex[:8]}",
            "fecha_nacimiento": "1985-03-20",
        }, headers=auth_header_teacher)
        assert resp.status_code == 201
        assert "creado" in resp.json().get("message", "").lower()

    def test_create_user_duplicate(self, client, auth_header_teacher):
        username = f"dup-user-{uuid.uuid4().hex[:8]}"
        payload = {
            "username": username,
            "email": f"dup@test.com",
            "password": "Test1234!",
            "role": "Estudiantes",
            "nombre": "Dup",
            "cedula": f"17{uuid.uuid4().hex[:8]}",
            "fecha_nacimiento": "2000-01-01",
        }
        client.post(self.URL, json=payload, headers=auth_header_teacher)
        resp = client.post(self.URL, json=payload, headers=auth_header_teacher)
        assert resp.status_code == 400

    def test_create_user_invalid_role(self, client, auth_header_teacher):
        resp = client.post(self.URL, json={
            "username": "invalid-role",
            "email": "inv@test.com",
            "password": "Test1234!",
            "role": "Admin",
            "nombre": "Invalid",
            "cedula": "12345",
            "fecha_nacimiento": "2000-01-01",
        }, headers=auth_header_teacher)
        assert resp.status_code == 400  # Manual validation by endpoint


class TestAdminAuditAll:
    """GET /admin/audit/all"""

    URL = "/admin/audit/all"

    def test_audit_unauthorized(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_audit_student_forbidden(self, client, auth_header_student):
        resp = client.get(self.URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_audit_teacher_empty(self, client, auth_header_teacher):
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
