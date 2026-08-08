"""
Contract tests for the GET /api/ping endpoint
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_ping_returns_pong():
    """Test that /api/ping returns the expected pong response"""
    response = client.get("/api/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "pong", "service": "tcyberchat"}
