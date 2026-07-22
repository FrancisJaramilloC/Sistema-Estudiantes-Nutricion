"""
Tests for the admin routes (users, tasks, audit).

Uses moto-mocked DynamoDB and mock auth tokens.
"""

import bcrypt
import uuid


class TestAdminTasks:
    """GET /admin/tasks"""

    URL = "/admin/tasks"

    def test_list_tasks_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to list all tasks."""
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_tasks_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to list tasks."""
        resp = client.get(self.URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_list_tasks_unauthorized(self, client):
        """Without auth, listing tasks should be unauthorized (401)."""
        resp = client.get(self.URL)
        assert resp.status_code == 401


class TestAdminUsers:
    """GET /admin/users"""

    URL = "/admin/users"

    def _register_user(self, client, username="admin_test_user"):
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "MyPass123!",
            "role": "Estudiantes",
            "nombre": "Test User",
            "cedula": "8888888888",
            "fecha_nacimiento": "2000-01-01",
        }
        client.post("/auth/register", json=payload)

    def test_list_users_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to list users."""
        self._register_user(client)
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        users = resp.json()
        # Should include the registered user (passwords should be masked)
        usernames = [u["username"] for u in users]
        assert "admin_test_user" in usernames
        # Password should not be in response
        for u in users:
            assert "password" not in u

    def test_list_users_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to list users."""
        resp = client.get(self.URL, headers=auth_header_student)
        assert resp.status_code == 403


class TestAdminDeleteUser:
    """DELETE /admin/users/{username}"""

    def _register_user(self, client, username="del_user"):
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "MyPass123!",
            "role": "Estudiantes",
            "nombre": "Delete User",
            "cedula": "9999999999",
            "fecha_nacimiento": "2000-01-01",
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201

    def test_delete_user_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to delete a student user."""
        self._register_user(client)
        resp = client.delete("/admin/users/del_user", headers=auth_header_teacher)
        assert resp.status_code == 200
        assert "eliminado" in resp.json()["message"]

    def test_delete_nonexistent_user(self, client, auth_header_teacher):
        """Deleting a non-existent user should return 404."""
        resp = client.delete("/admin/users/ghost_user", headers=auth_header_teacher)
        assert resp.status_code == 404

    def test_delete_self_forbidden(self, client, auth_header_teacher):
        """A teacher should NOT be able to delete themselves (docente_prueba)."""
        resp = client.delete("/admin/users/docente_prueba", headers=auth_header_teacher)
        assert resp.status_code == 400

    def test_delete_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to delete users."""
        resp = client.delete("/admin/users/someone", headers=auth_header_student)
        assert resp.status_code == 403


class TestAdminUpdateRole:
    """PUT /admin/users/{username}/role"""

    def _register_user(self, client, username="role_user"):
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "password": "MyPass123!",
            "role": "Estudiantes",
            "nombre": "Role User",
            "cedula": "1010101010",
            "fecha_nacimiento": "2000-01-01",
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201

    def test_update_role_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to update a user's role."""
        self._register_user(client)
        resp = client.put(
            "/admin/users/role_user/role",
            json={"role": "Docentes"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 200
        assert "actualizado" in resp.json()["message"]

    def test_update_self_role_forbidden(self, client, auth_header_teacher):
        """A teacher should NOT be able to update their own role."""
        resp = client.put(
            "/admin/users/docente_prueba/role",
            json={"role": "Estudiantes"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 400

    def test_update_role_invalid_value(self, client, auth_header_teacher):
        """An invalid role value should return 400."""
        resp = client.put(
            "/admin/users/some_user/role",
            json={"role": "Admin"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 400

    def test_update_role_nonexistent_user(self, client, auth_header_teacher):
        """Updating role for a non-existent user should return 404."""
        resp = client.put(
            "/admin/users/ghost/role",
            json={"role": "Docentes"},
            headers=auth_header_teacher,
        )
        assert resp.status_code == 404


class TestAdminAudit:
    """GET /admin/audit/login-events"""

    URL = "/admin/audit/login-events"

    def test_audit_as_teacher(self, client, auth_header_teacher):
        """A teacher should be able to view audit events."""
        # Perform a login to create an audit event
        client.post("/auth/login", json={"username": "nobody", "password": "wrong"})

        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        events = resp.json()
        assert isinstance(events, list)

    def test_audit_as_student_forbidden(self, client, auth_header_student):
        """A student should NOT be able to view audit events."""
        resp = client.get(self.URL, headers=auth_header_student)
        assert resp.status_code == 403

    def test_audit_unauthorized(self, client):
        """Without auth, audit events should be unauthorized (401)."""
        resp = client.get(self.URL)
        assert resp.status_code == 401
