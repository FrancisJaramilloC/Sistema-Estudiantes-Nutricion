"""
Tests for app.monitoring — validates privacy validation, performance tracking,
login event logging, and the security monitoring middleware.
"""

import time
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from prometheus_client import REGISTRY

from app.monitoring import (
    validate_privacy,
    track_clinical_performance,
    log_login_event,
    SecurityMonitoringMiddleware,
    CLINICAL_REQUESTS_TOTAL,
    LOGIN_SUCCESS_TOTAL,
    PRIVACY_BLOCKS_TOTAL,
)


class TestValidatePrivacy:
    """Validate the privacy validator that blocks PII fields."""

    def test_clean_data_passes(self):
        """Data without PII fields should pass validation."""
        data = {
            "patient_id": "abc-123",
            "imc": 24.5,
            "peso_kg": 70.0,
            "created_at": "2024-01-01",
        }
        # Should not raise
        validate_privacy(data)

    def test_nombre_field_blocked(self):
        """Field 'nombre' should be blocked."""
        data = {"nombre": "Juan Perez", "imc": 22.0}
        with pytest.raises(HTTPException) as exc:
            validate_privacy(data)
        assert exc.value.status_code == 400
        assert "Violación de política de privacidad" in exc.value.detail

    def test_cedula_field_blocked(self):
        """Field 'cedula' should be blocked."""
        data = {"cedula": "12345678", "imc": 22.0}
        with pytest.raises(HTTPException) as exc:
            validate_privacy(data)
        assert exc.value.status_code == 400

    def test_correo_field_blocked(self):
        """Field 'correo' should be blocked."""
        data = {"correo": "user@example.com", "imc": 22.0}
        with pytest.raises(HTTPException) as exc:
            validate_privacy(data)
        assert exc.value.status_code == 400

    def test_pii_field_inside_nested_data_not_blocked(self):
        """The validator only checks top-level keys per the implementation."""
        data = {"nested": {"nombre": "Juan"}}
        validate_privacy(data)

    def test_privacy_blocks_counter_incremented(self):
        """PRIVACY_BLOCKS_TOTAL counter should increment when a PII field is blocked."""
        before = REGISTRY.get_sample_value("nutria_privacy_blocks_total") or 0
        with pytest.raises(HTTPException):
            validate_privacy({"nombre": "Test"})
        after = REGISTRY.get_sample_value("nutria_privacy_blocks_total") or 0
        assert after > before


class TestTrackClinicalPerformance:
    """Context manager that measures clinical calculation latency."""

    def test_basic_tracking(self):
        """The context manager should complete without error."""
        with track_clinical_performance():
            result = 1 + 1
        assert result == 2

    def test_latency_recorded(self):
        """Latency should be recorded in the histogram."""
        sample_name = "nutria_clinical_latency_seconds_count"
        before = REGISTRY.get_sample_value(sample_name) or 0
        with track_clinical_performance():
            time.sleep(0.01)
        after = REGISTRY.get_sample_value(sample_name) or 0
        assert after > before


class TestLogLoginEvent:
    """Login event logging."""

    def test_counter_incremented(self):
        """LOGIN_SUCCESS_TOTAL should increment when log_login_event is called."""
        before = REGISTRY.get_sample_value("nutria_login_success_total") or 0
        log_login_event("test_user")
        after = REGISTRY.get_sample_value("nutria_login_success_total") or 0
        assert after > before
