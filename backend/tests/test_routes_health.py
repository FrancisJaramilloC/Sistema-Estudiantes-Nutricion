"""
Tests for the health check route.
"""


class TestHealthCheck:
    def test_health_returns_online(self, client):
        """GET / should return status online."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == "nutria-api"

    def test_health_is_fast(self, client):
        """Health check should respond quickly."""
        response = client.get("/")
        assert response.elapsed.total_seconds() < 2.0
