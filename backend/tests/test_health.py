"""
Tests for GET /api/health endpoint.

Uses FastAPI's TestClient (backed by httpx) for synchronous testing.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for the /api/health endpoint."""

    def test_health_returns_200(self) -> None:
        """Health endpoint must return HTTP 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_json(self) -> None:
        """Response must be valid JSON."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data, dict)

    def test_health_status_field(self) -> None:
        """Response must contain status == 'healthy'."""
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_service_field(self) -> None:
        """Response must contain a non-empty service field."""
        response = client.get("/api/health")
        data = response.json()
        assert "service" in data
        assert "TaskPilot" in data["service"]

    def test_health_version_field(self) -> None:
        """Response must include a version string."""
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_environment_field(self) -> None:
        """Response must include an environment string."""
        response = client.get("/api/health")
        data = response.json()
        assert "environment" in data
        assert isinstance(data["environment"], str)

    def test_health_timestamp_field(self) -> None:
        """Response must include a UTC timestamp."""
        response = client.get("/api/health")
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_openapi_schema_accessible(self) -> None:
        """OpenAPI JSON schema endpoint must be reachable."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_docs_accessible(self) -> None:
        """Swagger UI docs endpoint must be reachable."""
        response = client.get("/docs")
        assert response.status_code == 200
