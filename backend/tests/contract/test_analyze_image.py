"""
Contract tests for POST /api/analyze-image endpoint
Tests image analysis functionality using multi-modal AI
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_analyze_image_success():
    """Test successful image analysis"""
    # Create a minimal PNG image (1x1 transparent pixel)
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {"image": ("test.png", png_content, "image/png")}

    response = client.post("/api/analyze-image", files=files)

    # Should fail until endpoint is implemented
    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "description" in response_data
    assert "objects" in response_data
    assert "confidence" in response_data
    assert isinstance(response_data["description"], str)
    assert isinstance(response_data["objects"], list)
    assert isinstance(response_data["confidence"], (int, float))

def test_analyze_image_with_query():
    """Test image analysis with specific query"""
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {"image": ("chart.png", png_content, "image/png")}
    data = {"query": "What does this chart show?"}

    response = client.post("/api/analyze-image", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()

    assert "description" in response_data
    assert "answer" in response_data
    assert isinstance(response_data["answer"], str)

def test_analyze_image_no_file():
    """Test image analysis with no image file"""
    response = client.post("/api/analyze-image")

    # Should return validation error
    assert response.status_code == 422

def test_analyze_image_unsupported_format():
    """Test image analysis with unsupported file format"""
    # Text file instead of image
    text_content = b"This is not an image file"
    files = {"image": ("test.txt", text_content, "text/plain")}

    response = client.post("/api/analyze-image", files=files)

    # Should return unsupported media type
    assert response.status_code == 415

def test_analyze_image_corrupted():
    """Test image analysis with corrupted image data"""
    corrupted_content = b"This is not a valid image"
    files = {"image": ("corrupted.jpg", corrupted_content, "image/jpeg")}

    response = client.post("/api/analyze-image", files=files)

    # Should return bad request or processing error
    assert response.status_code in [400, 422, 500]

def test_analyze_image_too_large():
    """Test image analysis with file exceeding size limit"""
    # Create content larger than 10MB limit
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"image": ("large.png", large_content, "image/png")}

    response = client.post("/api/analyze-image", files=files)

    # Should return payload too large error
    assert response.status_code == 413