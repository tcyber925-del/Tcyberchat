"""
Contract tests for the GET /api/status endpoint
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_status_returns_running():
    """Test that /api/status returns the expected status response"""
    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {"status": "running", "service": "tcyberchat", "version": "1.0.0"}
