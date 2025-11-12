"""
Contract tests for POST /api/documents endpoint
Tests document upload functionality
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_documents_upload_success():
    """Test successful document upload"""
    # Create a sample text file content
    file_content = b"This is a test document for upload."
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post("/api/documents", files=files)

    # Should fail until endpoint is implemented
    assert response.status_code == 201
    response_data = response.json()

    # Validate response structure
    assert "documentId" in response_data
    assert "filename" in response_data
    assert "size" in response_data
    assert "status" in response_data
    assert response_data["filename"] == "test.txt"
    assert response_data["size"] == len(file_content)
    assert response_data["status"] == "processing"


def test_documents_upload_pdf():
    """Test PDF document upload"""
    # Mock PDF content (simplified)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}

    response = client.post("/api/documents", files=files)

    assert response.status_code == 201
    response_data = response.json()

    assert "documentId" in response_data
    assert response_data["filename"] == "test.pdf"
    assert response_data["status"] == "processing"


def test_documents_upload_no_file():
    """Test upload request with no file"""
    response = client.post("/api/documents")

    # Should return validation error
    assert response.status_code == 422


def test_documents_upload_unsupported_format():
    """Test upload of unsupported file format"""
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    files = {"file": ("test.exe", exe_content, "application/x-msdownload")}

    response = client.post("/api/documents", files=files)

    # Should reject unsupported format
    assert response.status_code == 415  # Unsupported Media Type


def test_documents_upload_file_too_large():
    """Test upload of file exceeding size limit"""
    # Create content larger than 50MB limit
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    files = {"file": ("large.txt", large_content, "text/plain")}

    response = client.post("/api/documents", files=files)

    # Should return payload too large error
    assert response.status_code == 413  # Payload Too Large
