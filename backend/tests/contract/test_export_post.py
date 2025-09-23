"""
Contract tests for POST /api/export endpoint
Tests data export functionality
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_export_full_success():
    """Test successful full data export"""
    request_data = {
        "includeDocuments": True,
        "includeEmbeddings": False
    }

    response = client.post("/api/export", json=request_data)

    # Should fail until endpoint is implemented
    assert response.status_code == 200

    # Check response headers for file download
    assert "content-disposition" in response.headers
    assert "attachment" in response.headers["content-disposition"]
    assert "filename=" in response.headers["content-disposition"]

    # Should return binary data
    assert response.content is not None
    assert len(response.content) > 0

def test_export_metadata_only():
    """Test export with documents excluded"""
    request_data = {
        "includeDocuments": False,
        "includeEmbeddings": False
    }

    response = client.post("/api/export", json=request_data)

    assert response.status_code == 200

    # File should be smaller without documents
    assert len(response.content) > 0

def test_export_with_date_filter():
    """Test export with date range filtering"""
    request_data = {
        "includeDocuments": True,
        "includeEmbeddings": False,
        "dateRange": {
            "start": "2025-01-01",
            "end": "2025-12-31"
        }
    }

    response = client.post("/api/export", json=request_data)

    assert response.status_code == 200
    assert len(response.content) > 0

def test_export_empty_database():
    """Test export when no data exists"""
    request_data = {
        "includeDocuments": True,
        "includeEmbeddings": True
    }

    response = client.post("/api/export", json=request_data)

    # Should still succeed even with empty data
    assert response.status_code == 200
    # Content might be minimal but should exist
    assert response.content is not None

def test_export_invalid_date_range():
    """Test export with invalid date range"""
    request_data = {
        "includeDocuments": True,
        "dateRange": {
            "start": "2025-12-31",
            "end": "2025-01-01"  # End before start
        }
    }

    response = client.post("/api/export", json=request_data)

    # Should return validation error
    assert response.status_code == 422