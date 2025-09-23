"""
Audio transcription API endpoints for speech-to-text processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import base64
import io

from ..database import get_db
from ..services.multimodal_service import MultiModalService

router = APIRouter(prefix="", tags=["transcribe-audio"])

class AudioTranscriptionRequest(BaseModel):
    """Request model for audio transcription"""
    audio_data: str  # Base64 encoded audio data
    language: Optional[str] = None  # Language code (e.g., 'en', 'es', 'fr')
    document_id: Optional[str] = None  # Associated document ID if applicable
    include_timestamps: Optional[bool] = False  # Include word-level timestamps

class AudioTranscriptionResponse(BaseModel):
    """Response model for audio transcription"""
    transcription: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    duration: Optional[float] = None  # Audio duration in seconds
    segments: Optional[List[Dict[str, Any]]] = None  # Timestamped segments
    document_id: Optional[str] = None

@router.post("/transcribe-audio", response_model=AudioTranscriptionResponse)
async def transcribe_audio(
    request: AudioTranscriptionRequest,
    db: Session = Depends(get_db)
) -> AudioTranscriptionResponse:
    """
    Transcribe audio content to text using speech recognition.

    Supports multiple languages and optional timestamp generation.
    """
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform audio transcription
        transcription_result = await multimodal_service.transcribe_audio(
            audio_data=audio_bytes,
            language=request.language,
            document_id=request.document_id,
            include_timestamps=request.include_timestamps
        )

        return AudioTranscriptionResponse(
            transcription=transcription_result["transcription"],
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language", request.language),
            duration=transcription_result.get("duration"),
            segments=transcription_result.get("segments"),
            document_id=request.document_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")

@router.post("/transcribe-audio/upload", response_model=AudioTranscriptionResponse)
async def transcribe_uploaded_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    document_id: Optional[str] = None,
    include_timestamps: Optional[bool] = False,
    db: Session = Depends(get_db)
) -> AudioTranscriptionResponse:
    """
    Transcribe an uploaded audio file to text.

    Alternative endpoint that accepts multipart file uploads.
    """
    try:
        # Validate file type
        valid_audio_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave',
            'audio/flac', 'audio/ogg', 'audio/aac', 'audio/m4a'
        ]

        if file.content_type not in valid_audio_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {', '.join(valid_audio_types)}"
            )

        # Read file content
        audio_bytes = await file.read()

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform audio transcription
        transcription_result = await multimodal_service.transcribe_audio(
            audio_data=audio_bytes,
            language=language,
            document_id=document_id,
            include_timestamps=include_timestamps
        )

        return AudioTranscriptionResponse(
            transcription=transcription_result["transcription"],
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language", language),
            duration=transcription_result.get("duration"),
            segments=transcription_result.get("segments"),
            document_id=document_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")

@router.get("/transcribe-audio/languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages for audio transcription.
    """
    try:
        multimodal_service = MultimodalService()
        languages = await multimodal_service.get_supported_languages()

        return {
            "languages": languages,
            "default_language": "en",
            "note": "Language auto-detection is supported if no language is specified"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language info: {str(e)}")

@router.get("/transcribe-audio/models")
async def get_transcription_models() -> Dict[str, Any]:
    """
    Get information about available transcription models.
    """
    try:
        multimodal_service = MultimodalService()
        models = await multimodal_service.get_transcription_models()

        return {
            "models": models,
            "default_model": "whisper-base",  # or whatever the default is
            "supported_formats": ["mp3", "wav", "flac", "ogg", "aac", "m4a"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.post("/analyze-audio")
async def analyze_audio_content(
    request: AudioTranscriptionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze audio content beyond transcription (sentiment, speakers, etc.).
    """
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform audio analysis
        analysis_result = await multimodal_service.analyze_audio_content(
            audio_data=audio_bytes,
            document_id=request.document_id
        )

        return {
            "transcription": analysis_result.get("transcription", ""),
            "sentiment": analysis_result.get("sentiment"),
            "speakers": analysis_result.get("speakers", []),
            "topics": analysis_result.get("topics", []),
            "language": analysis_result.get("language"),
            "duration": analysis_result.get("duration"),
            "document_id": request.document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")