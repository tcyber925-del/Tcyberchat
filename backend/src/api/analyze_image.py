"""
Image analysis API endpoints for multi-modal processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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

@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
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

        # Extract text
        text_result = await multimodal_service.extract_text_from_image(
            image_data=image_bytes,
            document_id=request.document_id
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