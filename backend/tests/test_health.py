"""
Contract tests for the simple GET /health endpoint
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_simple_status():
    """Test that /health returns the simple liveness payload"""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}
