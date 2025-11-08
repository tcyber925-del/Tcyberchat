"""
Contract tests for POST /api/chat endpoint
Tests the chat message sending functionality
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_post_success():
    """Test successful chat message posting"""
    request_data = {
        "message": "Hello, how are you?"
    }

    response = client.post("/chat/", json=request_data)

    # This test should fail initially since the endpoint doesn't exist yet
    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "response" in response_data
    assert "messageId" in response_data
    assert isinstance(response_data["response"], str)
    assert len(response_data["response"]) > 0

def test_chat_post_with_document_context():
    """Test chat with document context"""
    request_data = {
        "message": "What are the main topics discussed?",
        "documentId": "550e8400-e29b-41d4-a716-446655440000"
    }

    response = client.post("/chat/", json=request_data)

    # Should fail until endpoint is implemented
    assert response.status_code == 200
    response_data = response.json()

    assert "response" in response_data
    assert "messageId" in response_data
    assert isinstance(response_data["response"], str)

def test_chat_post_empty_message():
    """Test chat with empty message - should fail validation"""
    request_data = {
        "message": ""
    }

    response = client.post("/chat/", json=request_data)

    # Should return validation error
    assert response.status_code == 422  # Unprocessable Entity

def test_chat_post_invalid_document_id():
    """Test chat with invalid document ID"""
    request_data = {
        "message": "Test message",
        "documentId": "invalid-uuid"
    }

    response = client.post("/chat/", json=request_data)

    # Should return validation error for invalid UUID
    assert response.status_code == 422

def test_chat_post_missing_message():
    """Test chat request missing message field"""
    request_data = {}

    response = client.post("/chat/", json=request_data)

    # Should return validation error
    assert response.status_code == 422