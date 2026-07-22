"""
Tests for app.auth — validates JWT token handling, role-based access control.
"""

from unittest.mock import patch, MagicMock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import config
from app.auth import get_current_user, require_role


class TestGetCurrentUser:
    def test_valid_local_jwt(self):
        """A JWT signed with the local secret should decode correctly."""
        payload = {
            "username": "test_user",
            "cognito:groups": ["Estudiantes"],
            "email": "test@example.com",
        }
        token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        result = get_current_user(creds)
        assert result["username"] == "test_user"
        assert "Estudiantes" in result["cognito:groups"]

    def test_mock_teacher_token(self):
        """The mock-teacher-token should return a teacher user."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-teacher-token")
        result = get_current_user(creds)
        assert result["username"] == "docente_prueba"
        assert "Docentes" in result["cognito:groups"]

    def test_mock_student_token(self):
        """The mock-student-token should return a student user."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-student-token")
        result = get_current_user(creds)
        assert result["username"] == "estudiante_prueba"
        assert "Estudiantes" in result["cognito:groups"]

    def test_invalid_token_raises(self):
        """A garbage token should raise HTTP 401."""
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage-token")
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


class TestRequireRole:
    def test_teacher_allowed_for_teacher(self):
        """A user in Docentes should pass require_role([\"Docentes\"])."""
        dep = require_role(["Docentes"])
        user = {"username": "teacher1", "cognito:groups": ["Docentes"]}
        result = dep(user)
        assert result == user

    def test_student_allowed_for_student(self):
        """A user in Estudiantes should pass require_role([\"Estudiantes\"])."""
        dep = require_role(["Estudiantes"])
        user = {"username": "student1", "cognito:groups": ["Estudiantes"]}
        result = dep(user)
        assert result == user

    def test_student_denied_for_teacher_only(self):
        """A student should be denied access to teacher-only endpoint."""
        dep = require_role(["Docentes"])
        user = {"username": "student1", "cognito:groups": ["Estudiantes"]}
        with pytest.raises(HTTPException) as exc:
            dep(user)
        assert exc.value.status_code == 403

    def test_teacher_denied_nonexistent_group(self):
        """A user without any matching group should get 403."""
        dep = require_role(["Admin"])
        user = {"username": "user1", "cognito:groups": ["Estudiantes"]}
        with pytest.raises(HTTPException) as exc:
            dep(user)
        assert exc.value.status_code == 403

    def test_no_groups_falls_back_to_estudiantes(self):
        """If cognito:groups is missing, default is Estudiantes."""
        dep = require_role(["Docentes"])
        user = {"username": "user1"}
        with pytest.raises(HTTPException) as exc:
            dep(user)
        assert exc.value.status_code == 403

    def test_student_allowed_for_any_role(self):
        """A student should be allowed when both Estudiantes and Docentes are in allowed_groups."""
        dep = require_role(["Estudiantes", "Docentes"])
        user = {"username": "student1", "cognito:groups": ["Estudiantes"]}
        result = dep(user)
        assert result == user

    def test_teacher_allowed_for_any_role(self):
        """A teacher should be allowed when both grupos are in allowed_groups."""
        dep = require_role(["Estudiantes", "Docentes"])
        user = {"username": "teacher1", "cognito:groups": ["Docentes"]}
        result = dep(user)
        assert result == user
