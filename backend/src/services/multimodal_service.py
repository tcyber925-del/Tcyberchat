"""
MultiModalService for image analysis, audio transcription, and rich content processing
"""

from typing import Dict, List, Optional, Any, Tuple
import base64
import io
from pathlib import Path

try:
    # Image processing
    from PIL import Image
    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM

    # Audio processing
    import whisper

    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

from .ai_service import get_ai_service


class MultiModalService:
    """Service for multi-modal content processing (images, audio, rich content)"""

    def __init__(self):
        self.ai_service = get_ai_service()

        # Initialize models (lazy loading)
        self._image_model = None
        self._image_processor = None
        self._audio_model = None

    async def _ensure_image_model(self):
        """Lazy load image analysis model"""
        if not MULTIMODAL_AVAILABLE or self._image_model is not None:
            return

        try:
            # Use a lightweight vision model (placeholder - would use actual model)
            # In production, this would load something like LLaVA or similar
            print("Image model would be loaded here")
        except Exception as e:
            print(f"Failed to load image model: {e}")

    async def _ensure_audio_model(self):
        """Lazy load audio transcription model"""
        if not MULTIMODAL_AVAILABLE or self._audio_model is not None:
            return

        try:
            # Load Whisper model for transcription
            self._audio_model = whisper.load_model("base")
        except Exception as e:
            print(f"Failed to load audio model: {e}")

    async def analyze_image(self, image_data: bytes, prompt: Optional[str] = None, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze image using vision-language model"""
        await self._ensure_image_model()

        try:
            # Attempt to open bytes as an image to validate content
            from PIL import Image
            try:
                img2 = Image.open(io.BytesIO(image_data))
                width, height = img2.size
                mock_description = f"Image of size {width}x{height}."
            except Exception:
                # If PIL cannot open, treat as corrupted
                raise ValueError("Invalid or corrupted image data")

            mock_objects = ["object1", "object2"]

            # Use AI service for any additional prompt processing
            answer = None
            if prompt:
                enhanced_prompt = f"Based on this image analysis, {prompt}"
                try:
                    ai_response = await self.ai_service.generate_response(enhanced_prompt)
                    answer = ai_response.get("response") if isinstance(ai_response, dict) else str(ai_response)
                except Exception:
                    answer = None

            return {
                "description": mock_description,
                "objects": mock_objects,
                "answer": answer,
                "confidence": 0.85,
                "processing_time": 0.1
            }

        except Exception as e:
            return {
                "error": f"Image analysis failed: {str(e)}",
                "description": "Unable to analyze image",
                "objects": [],
                "confidence": 0.0,
                "processing_time": 0.0
            }

    async def analyze_image_from_bytes(self, image_bytes: bytes, query: Optional[str] = None) -> Dict[str, Any]:
        """Analyze image from byte data"""
        try:
            # Save temporarily for processing
            temp_path = f"/tmp/temp_image_{hash(image_bytes)}.jpg"
            with open(temp_path, "wb") as f:
                f.write(image_bytes)

            result = await self.analyze_image(temp_path, query)

            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

            return result

        except Exception as e:
            return {
                "error": f"Image analysis failed: {str(e)}",
                "description": "Unable to analyze image",
                "objects": [],
                "confidence": 0.0,
                "processing_time": 0.0
            }

    async def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None, document_id: Optional[str] = None, include_timestamps: bool = False) -> Dict[str, Any]:
        """Transcribe audio file to text"""
        await self._ensure_audio_model()

        try:
            # If model isn't available, return deterministic placeholder
            if not self._audio_model:
                # If a language parameter was provided, echo it back; otherwise unknown
                return {
                    "error": "Audio transcription model not available",
                    "transcription": "",
                    "segments": [],
                    "language": language or "unknown",
                    "processing_time": 0.0
                }

            # Save bytes to temp file and run transcription
            temp_path = f"temp_audio_{hash(audio_data)}.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_data)

            try:
                result = self._audio_model.transcribe(
                    temp_path,
                    language=language if language and language != "auto" else None,
                    verbose=False
                )
            finally:
                try:
                    Path(temp_path).unlink()
                except Exception:
                    pass

            # Format segments
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text")
                })

            return {
                "transcription": result.get("text", ""),
                "segments": segments,
                "language": result.get("language") or (language or "unknown"),
                "processing_time": result.get("processing_time", 0.0)
            }

        except Exception as e:
            return {
                "error": f"Audio transcription failed: {str(e)}",
                "transcription": "",
                "segments": [],
                "language": "unknown",
                "processing_time": 0.0
            }

    async def transcribe_audio_from_bytes(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio from byte data"""
        try:
            # Save temporarily for processing
            temp_path = f"/tmp/temp_audio_{hash(audio_bytes)}.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            result = await self.transcribe_audio(temp_path, language)

            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

            return result

        except Exception as e:
            return {
                "error": f"Audio transcription failed: {str(e)}",
                "transcription": "",
                "segments": [],
                "language": "unknown",
                "processing_time": 0.0
            }

    def render_rich_content(self, content: str, content_type: str,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render rich content for chat display"""
        try:
            metadata = metadata or {}

            if content_type == "markdown":
                # Process markdown (placeholder)
                rendered = f"<div class='markdown-content'>{content}</div>"

            elif content_type == "table":
                # Process table data (placeholder)
                rendered = f"<table class='chat-table'>{content}</table>"

            elif content_type == "code":
                # Syntax highlight code
                language = metadata.get("language", "text")
                rendered = f"<pre class='language-{language}'><code>{content}</code></pre>"

            elif content_type == "image":
                # Render image
                rendered = f"<img src='{content}' alt='Generated image' class='chat-image' />"

            else:
                # Plain text fallback
                rendered = f"<div class='chat-content'>{content}</div>"

            return {
                "renderedContent": rendered,
                "contentType": content_type,
                "metadata": metadata,
                "contentId": f"content_{hash(content)}"
            }

        except Exception as e:
            return {
                "error": f"Content rendering failed: {str(e)}",
                "renderedContent": f"<div class='error'>Failed to render content</div>",
                "contentType": content_type,
                "metadata": metadata or {}
            }

    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using OCR with pytesseract"""
        try:
            # Read image using PIL
            image = Image.open(image_path)

            # Convert PIL to numpy array for OpenCV preprocessing
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Preprocessing for better OCR
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Perform OCR
            text = pytesseract.image_to_string(threshold)

            # Get confidence data
            data = pytesseract.image_to_data(threshold, output_type=pytesseract.Output.DICT)

            # Calculate average confidence
            confidences = [conf for conf in data['conf'] if conf != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract text regions
            regions = []
            for i, conf in enumerate(data['conf']):
                if conf > 60:  # Only high confidence regions
                    regions.append({
                        "text": data['text'][i],
                        "confidence": conf,
                        "bbox": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    })

            return {
                "text": text.strip(),
                "confidence": avg_confidence / 100.0,  # Convert to 0-1 scale
                "language": "unknown",  # Could be detected
                "regions": regions
            }

        except Exception as e:
            return {
                "error": f"OCR failed: {str(e)}",
                "text": "",
                "confidence": 0.0,
                "language": "unknown",
                "regions": []
            }

    async def extract_text_from_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract text from image bytes using OCR"""
        try:
            # Create PIL image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Preprocessing for better OCR
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Perform OCR
            text = pytesseract.image_to_string(threshold)

            return {
                "text": text.strip(),
                "confidence": 0.8,  # Placeholder confidence
                "language": "unknown",
                "regions": []
            }

        except Exception as e:
            return {
                "error": f"OCR failed: {str(e)}",
                "text": "",
                "confidence": 0.0,
                "language": "unknown",
                "regions": []
            }

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported formats for each modality"""
        return {
            "images": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4"],
            "text": ["text/plain", "text/markdown", "application/pdf"]
        }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available image analysis models"""
        return [
            {
                "name": "ocr-tesseract",
                "type": "ocr",
                "description": "Tesseract OCR for text extraction",
                "languages": ["eng", "spa", "fra", "deu"]
            },
            {
                "name": "vision-placeholder",
                "type": "vision",
                "description": "Placeholder for vision model",
                "capabilities": ["object_detection", "scene_description"]
            }
        ]

    async def get_supported_languages(self) -> List[str]:
        """Get supported languages for transcription"""
        return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ar"]

    async def get_transcription_models(self) -> List[Dict[str, Any]]:
        """Get available transcription models"""
        return [
            {
                "name": "whisper-base",
                "size": "base",
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ar"],
                "description": "Fast Whisper model for general transcription"
            },
            {
                "name": "whisper-large",
                "size": "large",
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh", "ar"],
                "description": "High accuracy Whisper model"
            }
        ]

    async def analyze_audio_content(self, audio_data: bytes, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze audio content beyond transcription"""
        # First transcribe
        transcription_result = await self.transcribe_audio_from_bytes(audio_data)

        # Placeholder for additional analysis (sentiment, speakers, topics)
        return {
            "transcription": transcription_result.get("transcription", ""),
            "sentiment": "neutral",  # Placeholder
            "speakers": [],  # Placeholder for speaker diarization
            "topics": [],  # Placeholder for topic detection
            "language": transcription_result.get("language", "unknown"),
            "duration": transcription_result.get("processing_time", 0.0),
            "confidence": 0.8  # Placeholder
        }


# Global instance for dependency injection
_multimodal_service_instance = None

def get_multimodal_service() -> MultiModalService:
    """Get singleton MultiModalService instance"""
    global _multimodal_service_instance
    if _multimodal_service_instance is None:
        _multimodal_service_instance = MultiModalService()
    return _multimodal_service_instance