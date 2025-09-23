"""
Contract tests for POST /api/transcribe-audio endpoint
Tests audio transcription functionality
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_transcribe_audio_success():
    """Test successful audio transcription"""
    # Create minimal WAV file header + silence (44 bytes WAV header + some silence)
    wav_content = (
        b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        + b'\x00\x00\x80\x80\x00\x00\x80\x80'  # Some silence data
    )
    files = {"audio": ("test.wav", wav_content, "audio/wav")}

    response = client.post("/api/transcribe-audio", files=files)

    # Should fail until endpoint is implemented
    assert response.status_code == 200
    response_data = response.json()

    # Validate response structure
    assert "transcription" in response_data
    assert "segments" in response_data
    assert "language" in response_data
    assert isinstance(response_data["transcription"], str)
    assert isinstance(response_data["segments"], list)
    assert isinstance(response_data["language"], str)

def test_transcribe_audio_with_language():
    """Test audio transcription with explicit language"""
    wav_content = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00\x00\x00\x80\x80\x00\x00\x80\x80'
    files = {"audio": ("english.wav", wav_content, "audio/wav")}
    data = {"language": "en"}

    response = client.post("/api/transcribe-audio", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()

    assert "language" in response_data
    assert response_data["language"] == "en"

def test_transcribe_audio_mp3():
    """Test MP3 audio transcription"""
    # Minimal MP3 frame
    mp3_content = b'\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    files = {"audio": ("test.mp3", mp3_content, "audio/mpeg")}

    response = client.post("/api/transcribe-audio", files=files)

    assert response.status_code == 200
    response_data = response.json()

    assert "transcription" in response_data

def test_transcribe_audio_no_file():
    """Test audio transcription with no audio file"""
    response = client.post("/api/transcribe-audio")

    # Should return validation error
    assert response.status_code == 422

def test_transcribe_audio_unsupported_format():
    """Test audio transcription with unsupported format"""
    text_content = b"This is not audio data"
    files = {"audio": ("test.txt", text_content, "text/plain")}

    response = client.post("/api/transcribe-audio", files=files)

    # Should return unsupported media type
    assert response.status_code == 415

def test_transcribe_audio_too_large():
    """Test audio transcription with file exceeding size limit"""
    # Create content larger than 10MB limit
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {"audio": ("large.wav", large_content, "audio/wav")}

    response = client.post("/api/transcribe-audio", files=files)

    # Should return payload too large error
    assert response.status_code == 413

def test_transcribe_audio_corrupted():
    """Test audio transcription with corrupted audio data"""
    corrupted_content = b"This is not valid audio data"
    files = {"audio": ("corrupted.wav", corrupted_content, "audio/wav")}

    response = client.post("/api/transcribe-audio", files=files)

    # Should return processing error
    assert response.status_code in [400, 422, 500]

def test_transcribe_audio_empty():
    """Test audio transcription with empty audio file"""
    empty_wav = b'RIFF\x04\x00\x00\x00WAVE'  # Minimal empty WAV
    files = {"audio": ("empty.wav", empty_wav, "audio/wav")}

    response = client.post("/api/transcribe-audio", files=files)

    # Should succeed but transcription might be empty
    assert response.status_code == 200
    response_data = response.json()
    assert "transcription" in response_data
    # Transcription could be empty string for silence