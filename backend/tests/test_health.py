"""
Contract tests for the simple GET /health endpoint
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_simple_status():
    """Test that /health returns the simple liveness payload"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
