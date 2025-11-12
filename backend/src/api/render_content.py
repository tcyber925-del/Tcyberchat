"""
Content rendering API endpoints for multi-format document display
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.document import Document
from ..services.document_service import DocumentService

router = APIRouter(prefix="", tags=["render-content"])


class RenderRequest(BaseModel):
    """Request model for content rendering"""

    document_id: str
    format: str = "html"  # html, json, text, markdown
    include_metadata: bool = True
    highlight_terms: list[str] | None = None
    page: int | None = None  # For paginated content


class RenderOptions(BaseModel):
    """Options for content rendering"""

    theme: str | None = "default"
    font_size: str | None = "medium"
    show_line_numbers: bool | None = False
    syntax_highlighting: bool | None = True


@router.post("/render-content", response_class=HTMLResponse)
async def render_document_content(
    request: RenderRequest, options: RenderOptions = None, db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Render document content in various formats (HTML, JSON, text, markdown).

    Supports highlighting, theming, and pagination.
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Initialize document service
        document_service = DocumentService()

        # Render content based on format
        if request.format.lower() == "html":
            rendered_content = await document_service.render_as_html(
                document=document,
                include_metadata=request.include_metadata,
                highlight_terms=request.highlight_terms,
                options=options.dict() if options else None,
                page=request.page,
            )
            return HTMLResponse(content=rendered_content)

        elif request.format.lower() == "json":
            rendered_content = await document_service.render_as_json(
                document=document,
                include_metadata=request.include_metadata,
                page=request.page,
            )
            return JSONResponse(content=json.loads(rendered_content))

        elif request.format.lower() == "text":
            rendered_content = await document_service.render_as_text(
                document=document,
                include_metadata=request.include_metadata,
                page=request.page,
            )
            return StreamingResponse(
                content=iter([rendered_content]), media_type="text/plain"
            )

        elif request.format.lower() == "markdown":
            rendered_content = await document_service.render_as_markdown(
                document=document,
                include_metadata=request.include_metadata,
                page=request.page,
            )
            return StreamingResponse(
                content=iter([rendered_content]), media_type="text/markdown"
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Content rendering failed: {str(e)}"
        )


@router.get("/render-content/{document_id}/preview")
async def get_content_preview(
    document_id: str,
    max_length: int = Query(500, description="Maximum preview length"),
    include_metadata: bool = Query(True, description="Include metadata in preview"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get a preview of document content for quick display.
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Initialize document service
        document_service = DocumentService()

        # Generate preview
        preview = await document_service.generate_preview(
            document=document, max_length=max_length, include_metadata=include_metadata
        )

        return preview

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Preview generation failed: {str(e)}"
        )


@router.get("/render-content/formats")
async def get_supported_formats() -> dict[str, Any]:
    """
    Get list of supported rendering formats and their capabilities.
    """
    return {
        "formats": {
            "html": {
                "description": "Rich HTML with styling and interactive elements",
                "capabilities": ["highlighting", "theming", "pagination", "metadata"],
            },
            "json": {
                "description": "Structured JSON representation",
                "capabilities": ["metadata", "pagination", "structured_data"],
            },
            "text": {
                "description": "Plain text extraction",
                "capabilities": ["pagination", "metadata"],
            },
            "markdown": {
                "description": "Markdown formatted text",
                "capabilities": ["pagination", "metadata", "formatting"],
            },
        },
        "themes": ["default", "dark", "light", "high-contrast"],
        "font_sizes": ["small", "medium", "large"],
        "features": ["syntax_highlighting", "line_numbers", "search_highlighting"],
    }


@router.get("/render-content/{document_id}/pages")
async def get_document_pages(
    document_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Get pagination information for a document.
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Initialize document service
        document_service = DocumentService()

        # Get page information
        page_info = await document_service.get_page_info(document=document)

        return {
            "document_id": document_id,
            "total_pages": page_info["total_pages"],
            "page_size": page_info.get("page_size"),
            "has_pages": page_info["total_pages"] > 1,
            "estimated_total_length": page_info.get("estimated_total_length"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Page info retrieval failed: {str(e)}"
        )


@router.post("/render-content/extract")
async def extract_content_sections(
    document_id: str,
    sections: list[str] = None,
    format: str = "json",
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Extract specific sections or elements from document content.
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Initialize document service
        document_service = DocumentService()

        # Extract sections
        extracted_content = await document_service.extract_sections(
            document=document,
            sections=sections or ["headers", "paragraphs", "tables", "images"],
            format=format,
        )

        return extracted_content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Content extraction failed: {str(e)}"
        )


@router.get("/render-content/{document_id}/search")
async def search_within_document(
    document_id: str,
    query: str,
    case_sensitive: bool = False,
    whole_words: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Search for text within a specific document.
    """
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Initialize document service
        document_service = DocumentService()

        # Perform search
        search_results = await document_service.search_within_document(
            document=document,
            query=query,
            case_sensitive=case_sensitive,
            whole_words=whole_words,
        )

        return {
            "document_id": document_id,
            "query": query,
            "total_matches": len(search_results.get("matches", [])),
            "matches": search_results.get("matches", []),
            "context": search_results.get("context", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")
