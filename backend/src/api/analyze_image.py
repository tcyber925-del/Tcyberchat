"""
Image analysis API endpoints for multi-modal processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64
import io

from ..database import get_db
from ..services.multimodal_service import MultiModalService

router = APIRouter(prefix="", tags=["analyze-image"])

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    image_data: str  # Base64 encoded image data
    prompt: Optional[str] = None  # Custom analysis prompt
    document_id: Optional[str] = None  # Associated document ID if applicable

class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    analysis: str
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    document_id: Optional[str] = None

@router.post("/analyze-image/json", response_model=ImageAnalysisResponse)
async def analyze_image_json(
    request: ImageAnalysisRequest,
    db: Session = Depends(get_db)
) -> ImageAnalysisResponse:
    """
    Analyze an uploaded image using AI vision capabilities.

    Supports various analysis types including OCR, object detection,
    and contextual understanding.
    """
    try:
        # Decode base64 image data
        try:
            image_bytes = base64.b64decode(request.image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform image analysis
        analysis_result = await multimodal_service.analyze_image(
            image_data=image_bytes,
            prompt=request.prompt,
            document_id=request.document_id
        )

        return ImageAnalysisResponse(
            analysis=analysis_result["analysis"],
            confidence=analysis_result.get("confidence"),
            metadata=analysis_result.get("metadata", {}),
            document_id=request.document_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@router.post("/analyze-image/upload", response_model=ImageAnalysisResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = None,
    document_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> ImageAnalysisResponse:
    """
    Analyze an uploaded image file using AI vision capabilities.

    Alternative endpoint that accepts multipart file uploads.
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read file content
        image_bytes = await file.read()

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Perform image analysis
        analysis_result = await multimodal_service.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            document_id=document_id
        )

        return ImageAnalysisResponse(
            analysis=analysis_result["analysis"],
            confidence=analysis_result.get("confidence"),
            metadata=analysis_result.get("metadata", {}),
            document_id=document_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    query: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Multipart endpoint for image analysis expected by contract tests.

    Accepts form multipart with field name 'image' and optional form field 'query'.
    Enforces content-type and size limits and returns a simple analysis shape.
    """
    # Validate content type
    if not image.content_type or not image.content_type.startswith("image/"):
        # Unsupported media type
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File must be an image")

    # Read bytes and enforce size limit (10MB)
    image_bytes = await image.read()
    max_bytes = 10 * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image payload too large")

    try:
        multimodal_service = MultiModalService()
        # Use 'query' as prompt if provided
        result = await multimodal_service.analyze_image(image_data=image_bytes, prompt=query, document_id=document_id)

        # If the multimodal service indicates an error, surface as HTTP 400
        if isinstance(result, dict) and result.get("error"):
            raise ValueError(result.get("error"))

        # Normalize result to contract expected keys
        response: Dict[str, Any] = {
            "description": result.get("description") or result.get("analysis") or "",
            "objects": result.get("objects", []),
            "confidence": float(result.get("confidence", 0.0)),
        }

        # If test sent a query, include an 'answer' field
        if query:
            response["answer"] = result.get("answer") or result.get("analysis") or ""

        return response

    except ValueError as e:
        # Corrupted image / invalid image bytes
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        # Generic processing error
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@router.get("/analyze-image/models")
async def get_available_models() -> Dict[str, Any]:
    """
    Get information about available image analysis models.
    """
    try:
        multimodal_service = MultimodalService()
        models = await multimodal_service.get_available_models()

        return {
            "models": models,
            "default_model": "llava",  # or whatever the default is
            "supported_formats": ["jpeg", "png", "gif", "bmp", "tiff"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.post("/extract-text")
async def extract_text_from_image(
    request: ImageAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extract text content from images using OCR capabilities.
    """
    try:
        # Decode base64 image data
        try:
            image_bytes = base64.b64decode(request.image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Initialize multimodal service
        multimodal_service = MultimodalService()

        # Extract text using OCR
        text_result = await multimodal_service.extract_text_from_image_bytes(
            image_data=image_bytes
        )

        return {
            "text": text_result["text"],
            "confidence": text_result.get("confidence"),
            "language": text_result.get("language", "unknown"),
            "regions": text_result.get("regions", []),
            "document_id": request.document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")