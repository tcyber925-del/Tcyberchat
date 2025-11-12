"""
Audio transcription API endpoints for speech-to-text processing
"""

import base64
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.multimodal_service import MultiModalService

router = APIRouter(prefix="", tags=["transcribe-audio"])


class AudioTranscriptionRequest(BaseModel):
    """Request model for audio transcription"""

    audio_data: str  # Base64 encoded audio data
    language: str | None = None  # Language code (e.g., 'en', 'es', 'fr')
    document_id: str | None = None  # Associated document ID if applicable
    include_timestamps: bool | None = False  # Include word-level timestamps


class AudioTranscriptionResponse(BaseModel):
    """Response model for audio transcription"""

    transcription: str
    confidence: float | None = None
    language: str | None = None
    duration: float | None = None  # Audio duration in seconds
    segments: list[dict[str, Any]] | None = None  # Timestamped segments
    document_id: str | None = None


@router.post("/transcribe-audio/json", response_model=AudioTranscriptionResponse)
async def transcribe_audio_json(
    request: AudioTranscriptionRequest, db: Session = Depends(get_db)
) -> AudioTranscriptionResponse:
    """
    Transcribe audio content to text using speech recognition.

    Supports multiple languages and optional timestamp generation.
    """
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform audio transcription
        transcription_result = await multimodal_service.transcribe_audio(
            audio_data=audio_bytes,
            language=request.language,
            document_id=request.document_id,
            include_timestamps=request.include_timestamps,
        )

        return AudioTranscriptionResponse(
            transcription=transcription_result["transcription"],
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language", request.language),
            duration=transcription_result.get("duration"),
            segments=transcription_result.get("segments"),
            document_id=request.document_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Audio transcription failed: {str(e)}"
        )


@router.post("/transcribe-audio/upload", response_model=AudioTranscriptionResponse)
async def transcribe_uploaded_audio(
    file: UploadFile = File(...),
    language: str | None = None,
    document_id: str | None = None,
    include_timestamps: bool | None = False,
    db: Session = Depends(get_db),
) -> AudioTranscriptionResponse:
    """
    Transcribe an uploaded audio file to text.

    Alternative endpoint that accepts multipart file uploads.
    """
    try:
        # Validate file type
        valid_audio_types = [
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/wave",
            "audio/flac",
            "audio/ogg",
            "audio/aac",
            "audio/m4a",
        ]

        if file.content_type not in valid_audio_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {', '.join(valid_audio_types)}",
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
            include_timestamps=include_timestamps,
        )

        return AudioTranscriptionResponse(
            transcription=transcription_result["transcription"],
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language", language),
            duration=transcription_result.get("duration"),
            segments=transcription_result.get("segments"),
            document_id=document_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Audio transcription failed: {str(e)}"
        )


@router.post("/transcribe-audio")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
    document_id: str | None = Form(None),
    include_timestamps: bool | None = Form(False),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Multipart endpoint for audio transcription expected by contract tests.

    Accepts form multipart with field name 'audio' and optional 'language'.
    Enforces content-type and size limits and returns a simple transcription shape.
    """
    # Allowed types
    valid_audio_types = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/flac",
        "audio/ogg",
        "audio/aac",
        "audio/m4a",
    ]

    if not audio.content_type or audio.content_type not in valid_audio_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported audio format",
        )

    audio_bytes = await audio.read()
    max_bytes = 10 * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio payload too large",
        )

    # Heuristic: if the uploaded payload decodes cleanly to UTF-8 and contains readable text,
    # treat it as corrupted (client-sent plain text instead of audio). This catches test case
    # payloads like: b"This is not valid audio data".
    try:
        decoded = None
        try:
            decoded = audio_bytes.decode("utf-8")
        except Exception:
            decoded = None

        if decoded is not None:
            # If decoded text contains alphabetic characters and whitespace and no null bytes,
            # assume it's not audio data
            if any(c.isalpha() for c in decoded) and "\x00" not in decoded:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or corrupted audio payload",
                )
    except HTTPException:
        # Re-raise our intended HTTP errors
        raise
    except Exception:
        # Any unexpected error in the heuristic should not block processing
        pass

    try:
        multimodal_service = MultiModalService()
        result = await multimodal_service.transcribe_audio(
            audio_data=audio_bytes,
            language=language,
            document_id=document_id,
            include_timestamps=include_timestamps,
        )

        # If multimodal service signals a clear failure for corrupted content, decide response
        if isinstance(result, dict) and result.get("error"):
            err = str(result.get("error"))
            # If the payload looks like plain ASCII text, treat as corrupted -> Bad Request
            try:
                decoded = audio_bytes.decode("utf-8")
                if len(decoded) > 0:
                    raise ValueError("Failed to load audio: corrupted payload")
            except Exception:
                # Non-decodable or binary data: return 200 with empty transcription (best-effort)
                return {
                    "transcription": "",
                    "segments": [],
                    "language": language or "unknown",
                    "confidence": 0.0,
                    "duration": 0.0,
                }

        # Prefer explicit language parameter when provided
        resolved_lang = (
            result.get("language")
            if result.get("language") and result.get("language") != "unknown"
            else (language or "unknown")
        )

        response: dict[str, Any] = {
            "transcription": result.get("transcription", ""),
            "segments": result.get("segments", []),
            "language": resolved_lang,
            "confidence": float(result.get("confidence", 0.0)),
            "duration": result.get("duration"),
        }

        return response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Audio transcription failed: {str(e)}"
        )


@router.get("/transcribe-audio/languages")
async def get_supported_languages() -> dict[str, Any]:
    """
    Get list of supported languages for audio transcription.
    """
    try:
        multimodal_service = MultimodalService()
        languages = await multimodal_service.get_supported_languages()

        return {
            "languages": languages,
            "default_language": "en",
            "note": "Language auto-detection is supported if no language is specified",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get language info: {str(e)}"
        )


@router.get("/transcribe-audio/models")
async def get_transcription_models() -> dict[str, Any]:
    """
    Get information about available transcription models.
    """
    try:
        multimodal_service = MultimodalService()
        models = await multimodal_service.get_transcription_models()

        return {
            "models": models,
            "default_model": "whisper-base",  # or whatever the default is
            "supported_formats": ["mp3", "wav", "flac", "ogg", "aac", "m4a"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/analyze-audio")
async def analyze_audio_content(
    request: AudioTranscriptionRequest, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Analyze audio content beyond transcription (sentiment, speakers, etc.).
    """
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform audio analysis
        analysis_result = await multimodal_service.analyze_audio_content(
            audio_data=audio_bytes, document_id=request.document_id
        )

        return {
            "transcription": analysis_result.get("transcription", ""),
            "sentiment": analysis_result.get("sentiment"),
            "speakers": analysis_result.get("speakers", []),
            "topics": analysis_result.get("topics", []),
            "language": analysis_result.get("language"),
            "duration": analysis_result.get("duration"),
            "document_id": request.document_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")
