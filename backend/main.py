"""
Local First Chatbot Backend API
FastAPI application with multi-modal support, RAG, and local AI processing
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import time
import logging
import os
from typing import Callable

# Import API routers
try:
    from src.api.chat import router as chat_router
    from src.api.documents import router as documents_router
    from src.api.search import router as search_router
    from src.api.data_management import router as data_management_router
    from src.api.analyze_image import router as analyze_image_router
    from src.api.transcribe_audio import router as transcribe_audio_router
    from src.api.render_content import router as render_content_router

    # Import database utilities
    from src.database import get_database_status
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from src.api.chat import router as chat_router
    from src.api.documents import router as documents_router
    from src.api.search import router as search_router
    from src.api.data_management import router as data_management_router
    from src.api.analyze_image import router as analyze_image_router
    from src.api.transcribe_audio import router as transcribe_audio_router
    from src.api.render_content import router as render_content_router

    # Import database utilities
    from src.database import get_database_status

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title="Local First Chatbot API",
    description="""
    A comprehensive multi-modal chatbot API with local AI processing capabilities.

    ## Features

    * **Conversational AI**: Chat with RAG-enhanced responses using local LLM models
    * **Document Management**: Upload, process, and analyze various document types
    * **Multi-modal Processing**: Image analysis and audio transcription
    * **Vector Search**: Semantic search across document collections
    * **Data Portability**: Export/import functionality for data management

    ## Supported File Types

    * **Text Documents**: PDF, TXT, Markdown
    * **Images**: JPEG, PNG, GIF, WebP (with OCR and analysis)
    * **Audio**: MP3, WAV, OGG, MP4 (with transcription)

    ## Authentication

    Currently uses session-based authentication for multi-user support.

    ## Rate Limiting

    API endpoints include built-in rate limiting to prevent abuse.
    """,
    version="1.0.0",
    contact={
        "name": "Local First Chatbot",
        "url": "https://github.com/your-repo/local-chatbot",
        "email": "support@localchatbot.dev"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "chat",
            "description": "Conversational AI endpoints with RAG support"
        },
        {
            "name": "documents",
            "description": "Document upload, management, and processing"
        },
        {
            "name": "search",
            "description": "Vector search and retrieval across documents"
        },
        {
            "name": "data-management",
            "description": "Data export/import and backup operations"
        },
        {
            "name": "analyze-image",
            "description": "Image analysis and OCR capabilities"
        },
        {
            "name": "transcribe-audio",
            "description": "Audio transcription and analysis"
        },
        {
            "name": "render-content",
            "description": "Multi-format content rendering"
        }
    ],
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc documentation
    openapi_url="/openapi.json"  # OpenAPI JSON schema
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Log all HTTP requests and responses with timing"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")

    try:
        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_time:.3f}s)"
        )

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        # Log errors
        process_time = time.time() - start_time
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"-> {str(e)} ({process_time:.3f}s)"
        )
        raise

# Include API routers under a consistent /api base path to match contract tests
# Keep health and root endpoints at the top-level
app.include_router(chat_router, prefix="/api/chat")
# Also include chat router at top-level /chat for older tests that call /chat/
app.include_router(chat_router, prefix="/chat")
app.include_router(documents_router, prefix="/api/documents")
# Also include documents router at top-level /documents for tests that use that path
app.include_router(documents_router, prefix="/documents")
app.include_router(search_router, prefix="/api")
app.include_router(data_management_router, prefix="/api/data-management")
# Also provide legacy /api/export path expected by contract tests
app.include_router(data_management_router, prefix="/api")
app.include_router(analyze_image_router, prefix="/api")
app.include_router(transcribe_audio_router, prefix="/api")
app.include_router(render_content_router, prefix="/api")

# Global exception handlers for graceful error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url.path}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "type": "http_exception",
                "message": exc.detail,
                "status_code": exc.status_code
            },
            "request": {
                "method": request.method,
                "url": str(request.url)
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    # Sanitize Pydantic errors to avoid non-serializable inputs (e.g., bytes from multipart files)
    raw_errors = exc.errors()
    safe_errors = []
    for err in raw_errors:
        safe_err = dict(err)
        # Replace 'input' field if present and non-serializable
        inp = safe_err.get("input")
        try:
            # attempt a quick JSON-serializable check
            import json as _json
            _json.dumps(inp)
            safe_input = inp
        except Exception:
            # Replace bytes / large objects with a short description
            if isinstance(inp, (bytes, bytearray)):
                safe_input = f"<bytes length={len(inp)}>"
            else:
                safe_input = f"<{type(inp).__name__}>"
        if "input" in safe_err:
            safe_err["input"] = safe_input
        safe_errors.append(safe_err)

    logger.warning(f"Validation error: {safe_errors} - {request.url.path}")

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": safe_errors
            },
            "request": {
                "method": request.method,
                "url": str(request.url)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with graceful degradation"""
    logger.error(f"Unexpected error: {str(exc)} - {request.url.path}", exc_info=True)

    # Provide user-friendly error messages
    error_message = "An unexpected error occurred. Please try again later."
    if "database" in str(exc).lower():
        error_message = "Database temporarily unavailable. Please try again."
    elif "connection" in str(exc).lower():
        error_message = "Service temporarily unavailable. Please try again."
    elif "timeout" in str(exc).lower():
        error_message = "Request timed out. Please try again."

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_server_error",
                "message": error_message,
                "reference_id": f"ERR_{int(time.time())}"  # For support reference
            },
            "request": {
                "method": request.method,
                "url": str(request.url)
            }
        }
    )

# Graceful shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown gracefully"""
    logger.info("Application shutting down...")
    # Add any cleanup logic here (close connections, save state, etc.)

# Startup handler
@app.on_event("startup")
async def startup_event():
    """Handle application startup"""
    logger.info("Application starting up...")
    # Add any initialization logic here

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Local First Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check with real service status"""
    db_status = get_database_status()

    return {
        "status": "healthy" if db_status["overall_status"] == "healthy" else "degraded",
        "version": "1.0.0",
        "services": {
            "database": db_status["sqlalchemy"]["status"],
            "vector_store": db_status["chromadb"]["status"],
            "ollama": "not_checked"  # TODO: Add Ollama health check
        },
        "database_details": db_status
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True,
        log_level="info"
    )
