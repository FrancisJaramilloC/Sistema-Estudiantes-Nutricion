"""
Tests for the authentication routes (register, login, forgot-password, reset-password).

Uses moto-mocked DynamoDB and in-memory tables created by conftest.py.
"""

import bcrypt
import jwt as pyjwt
import datetime

from app import config


class TestRegister:
    """POST /auth/register"""

    REGISTER_URL = "/auth/register"

    def test_register_student_success(self, client):
        """Register a new student should return 201."""
        payload = {
            "username": "test_student",
            "email": "student@test.com",
            "password": "SecurePass123!",
            "role": "Estudiantes",
            "nombre": "Test Student",
            "cedula": "1234567890",
            "fecha_nacimiento": "2000-01-01",
        }
        resp = client.post(self.REGISTER_URL, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "registrado" in data["message"].lower()
        assert "test_student" in data["message"]

    def test_register_duplicate_username(self, client):
        """Registering with an existing username should return 400."""
        payload = {
            "username": "dup_user",
            "email": "dup1@test.com",
            "password": "SecurePass123!",
            "role": "Estudiantes",
            "nombre": "Dup User",
            "cedula": "1111111111",
            "fecha_nacimiento": "2000-01-01",
        }
        # First registration
        resp1 = client.post(self.REGISTER_URL, json=payload)
        assert resp1.status_code == 201

        # Second registration with same username
        payload2 = payload.copy()
        payload2["email"] = "dup2@test.com"
        payload2["cedula"] = "2222222222"
        resp2 = client.post(self.REGISTER_URL, json=payload2)
        assert resp2.status_code == 400
        assert "ya está registrado" in resp2.json()["detail"]

    def test_register_duplicate_email(self, client):
        """Registering with an existing email should return 400."""
        payload = {
            "username": "user_a",
            "email": "shared@test.com",
            "password": "SecurePass123!",
            "role": "Estudiantes",
            "nombre": "User A",
            "cedula": "3333333333",
            "fecha_nacimiento": "2000-01-01",
        }
        resp1 = client.post(self.REGISTER_URL, json=payload)
        assert resp1.status_code == 201

        payload2 = payload.copy()
        payload2["username"] = "user_b"
        payload2["cedula"] = "4444444444"
        resp2 = client.post(self.REGISTER_URL, json=payload2)
        assert resp2.status_code == 400
        assert "ya está registrado" in resp2.json()["detail"]

    def test_register_duplicate_cedula(self, client):
        """Registering with an existing cedula should return 400."""
        payload = {
            "username": "user_x",
            "email": "x@test.com",
            "password": "SecurePass123!",
            "role": "Estudiantes",
            "nombre": "User X",
            "cedula": "9999999999",
            "fecha_nacimiento": "2000-01-01",
        }
        resp1 = client.post(self.REGISTER_URL, json=payload)
        assert resp1.status_code == 201

        payload2 = payload.copy()
        payload2["username"] = "user_y"
        payload2["email"] = "y@test.com"
        resp2 = client.post(self.REGISTER_URL, json=payload2)
        assert resp2.status_code == 400
        assert "ya está registrada" in resp2.json()["detail"]


class TestLogin:
    """POST /auth/login"""

    LOGIN_URL = "/auth/login"

    def _register_user(self, client, username="login_user", password="MyPass123!"):
        """Helper to register a user before login tests."""
        payload = {
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
            "role": "Estudiantes",
            "nombre": "Login User",
            "cedula": "5555555555",
            "fecha_nacimiento": "2000-01-01",
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201

    def test_login_success(self, client):
        """Valid credentials should return access_token."""
        self._register_user(client)
        resp = client.post(self.LOGIN_URL, json={"username": "login_user", "password": "MyPass123!"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "id_token" in data
        assert data["expires_in"] == config.JWT_EXPIRATION_HOURS * 3600

    def test_login_wrong_password(self, client):
        """Wrong password should return 400."""
        self._register_user(client)
        resp = client.post(self.LOGIN_URL, json={"username": "login_user", "password": "WrongPass!"})
        assert resp.status_code == 400
        assert "incorrectos" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Logging in with a non-existent user should return 400."""
        resp = client.post(self.LOGIN_URL, json={"username": "ghost", "password": "AnyPass123!"})
        assert resp.status_code == 400
        assert "incorrectos" in resp.json()["detail"]

    def test_login_token_has_correct_claims(self, client):
        """The JWT returned should contain the user's claims."""
        self._register_user(client)
        resp = client.post(self.LOGIN_URL, json={"username": "login_user", "password": "MyPass123!"})
        token = resp.json()["access_token"]
        payload = pyjwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        assert payload["username"] == "login_user"
        assert payload["cognito:groups"] == ["Estudiantes"]
        assert payload["email"] == "login_user@test.com"


class TestForgotPassword:
    """POST /auth/forgot-password"""

    FORGOT_URL = "/auth/forgot-password"

    def _register_user(self, client, username="fp_user", email="fp@test.com"):
        payload = {
            "username": username,
            "email": email,
            "password": "MyPass123!",
            "role": "Estudiantes",
            "nombre": "FP User",
            "cedula": "6666666666",
            "fecha_nacimiento": "2000-01-01",
        }
        client.post("/auth/register", json=payload)

    def test_forgot_password_existing_email(self, client):
        """Requesting a reset token for an existing email should succeed."""
        self._register_user(client)
        resp = client.post(self.FORGOT_URL, json={"email": "fp@test.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert "reset_token" in data
        assert "username" in data
        assert data["username"] == "fp_user"

    def test_forgot_password_nonexistent_email(self, client):
        """Requesting a reset for an unknown email should return 200 with generic message (no user enumeration)."""
        resp = client.post(self.FORGOT_URL, json={"email": "nobody@test.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "reset_token" not in data

    def test_forgot_token_stored(self, client):
        """The reset token should be stored and retrievable."""
        self._register_user(client)
        resp = client.post(self.FORGOT_URL, json={"email": "fp@test.com"})
        data = resp.json()
        assert len(data["reset_token"]) > 0


class TestResetPassword:
    """POST /auth/reset-password"""

    RESET_URL = "/auth/reset-password"

    def _setup_reset(self, client):
        """Register user and get a reset token."""
        payload = {
            "username": "reset_user",
            "email": "reset@test.com",
            "password": "OldPass123!",
            "role": "Estudiantes",
            "nombre": "Reset User",
            "cedula": "7777777777",
            "fecha_nacimiento": "2000-01-01",
        }
        client.post("/auth/register", json=payload)
        fp_resp = client.post("/auth/forgot-password", json={"email": "reset@test.com"})
        fp_data = fp_resp.json()
        return fp_data["username"], fp_data["reset_token"]

    def test_reset_password_success(self, client):
        """A valid reset token should allow changing the password."""
        username, token = self._setup_reset(client)
        resp = client.post(
            self.RESET_URL,
            json={"username": username, "reset_token": token, "new_password": "NewPass456!"},
        )
        assert resp.status_code == 200
        assert "éxito" in resp.json()["message"]

    def test_reset_password_wrong_token(self, client):
        """An invalid reset token should return 400."""
        username, _ = self._setup_reset(client)
        resp = client.post(
            self.RESET_URL,
            json={"username": username, "reset_token": "invalid-token", "new_password": "NewPass456!"},
        )
        assert resp.status_code == 400

    def test_reset_password_nonexistent_user(self, client):
        """Resetting for a non-existent user should return 404."""
        resp = client.post(
            self.RESET_URL,
            json={"username": "ghost", "reset_token": "some-token", "new_password": "NewPass456!"},
        )
        assert resp.status_code == 404

    def test_reset_password_then_login(self, client):
        """After resetting, the new password should work for login."""
        username, token = self._setup_reset(client)
        # Reset to new password
        client.post(
            self.RESET_URL,
            json={"username": username, "reset_token": token, "new_password": "NewPass456!"},
        )
        # Login with new password should succeed
        resp = client.post("/auth/login", json={"username": username, "password": "NewPass456!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_reset_password_old_password_fails(self, client):
        """After resetting, the old password should no longer work."""
        username, token = self._setup_reset(client)
        client.post(
            self.RESET_URL,
            json={"username": username, "reset_token": token, "new_password": "NewPass456!"},
        )
        # Login with old password should fail
        resp = client.post("/auth/login", json={"username": username, "password": "OldPass123!"})
        assert resp.status_code == 400
