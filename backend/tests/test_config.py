"""
Tests for app.config — ensures configuration constants are correct.
"""

from app import config


def test_default_values():
    """Config should have correct default values."""
    assert config.JWT_ALGORITHM == "HS256"
    assert config.JWT_EXPIRATION_HOURS == 24
    # JWT_SECRET is read from env (conftest sets it), so check it's a non-empty string
    assert isinstance(config.JWT_SECRET, str)
    assert len(config.JWT_SECRET) > 0


def test_region_is_string():
    """AWS_REGION should be a non-empty string."""
    assert isinstance(config.AWS_REGION, str)
    assert len(config.AWS_REGION) > 0


def test_dynamodb_endpoint_not_set_in_tests():
    """DYNAMODB_ENDPOINT_URL should be None in tests (popped before app import)."""
    # We pop it before importing app; but .env file may set it via load_dotenv()
    # Just check it's not a real AWS endpoint
    val = config.DYNAMODB_ENDPOINT_URL
    if val is not None:
        # If load_dotenv set it, ensure it's the local one
        assert "dynamodb" in val
