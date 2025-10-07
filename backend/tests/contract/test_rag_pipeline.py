"""
Contract tests for RAG pipeline
Tests document upload and chat functionality
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
import os
import time
import uuid

client = TestClient(app)

def test_rag_pipeline():
    """Test RAG pipeline by uploading a document and asking a question"""
    # 1. Upload a document
    file_path = "backend/test_rag_doc.txt"
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    files = {"file": (os.path.basename(file_path), file_content, "text/plain")}
    response = client.post("/documents/", files=files)

    assert response.status_code == 200
    upload_data = response.json()
    document_id = upload_data["id"]

    # Poll for document processing to complete
    timeout = 60  # seconds
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = client.get(f"/documents/{document_id}")
        if response.status_code == 200 and response.json()["status"] == "completed":
            break
        time.sleep(1)
    else:
        pytest.fail("Document processing timed out")

    # 2. Send a chat message to ask a question about the document
    chat_message = {
        "message": "What is the capital of France?",
        "conversationId": str(uuid.uuid4()),  # Generate a valid UUID
        "model": "llama3.2:latest" # Specify an available Ollama model
    }

    response = client.post("/chat/", json=chat_message)
    
    assert response.status_code == 200
    chat_response = response.json()
    
    # 3. Verify the response from the RAG pipeline
    assert "Paris" in chat_response["response"]
