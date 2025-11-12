"""
Contract tests for POST /api/documents/{documentId}/summarize endpoint
Tests document summarization functionality
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_documents_summarize_success():
    """Test successful document summarization"""
    document_id = "550e8400-e29b-41d4-a716-446655440000"

    response = client.post(f"/api/documents/{document_id}/summarize")

    # Should fail until endpoint is implemented
    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "summary" in response_data
    assert "summaryId" in response_data
    assert "model" in response_data
    assert isinstance(response_data["summary"], str)
    assert len(response_data["summary"]) > 0


def test_documents_summarize_not_found():
    """Test summarization of non-existent document"""
    document_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(f"/api/documents/{document_id}/summarize")

    # Should return not found error
    assert response.status_code == 404


def test_documents_summarize_invalid_uuid():
    """Test summarization with invalid document ID format"""
    document_id = "invalid-uuid"

    response = client.post(f"/api/documents/{document_id}/summarize")

    # Should return validation error
    assert response.status_code == 422


def test_documents_summarize_not_ready():
    """Test summarization of document that hasn't finished processing"""
    document_id = "550e8400-e29b-41d4-a716-446655440001"

    response = client.post(f"/api/documents/{document_id}/summarize")

    # Should return unprocessable entity (document not ready)
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data


def test_documents_summarize_empty_document():
    """Test summarization of empty or very small document"""
    document_id = "550e8400-e29b-41d4-a716-446655440002"

    response = client.post(f"/api/documents/{document_id}/summarize")

    # Should still work but summary might be minimal
    assert response.status_code == 200
    response_data = response.json()
    assert "summary" in response_data
    # Summary should be a valid string (possibly indicating document is too short)
    assert isinstance(response_data["summary"], str)
