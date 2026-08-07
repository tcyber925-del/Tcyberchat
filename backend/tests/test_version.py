"""
Contract tests for the GET /api/version endpoint
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_version_returns_api_info():
    """Test that /api/version returns the API version payload"""
    response = client.get("/api/version")

    assert response.status_code == 200
    assert response.json() == {"version": "1.0.0", "status": "ok"}
