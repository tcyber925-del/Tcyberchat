"""
Search API endpoints for full-text and vector search
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.rag_service import get_rag_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search(
    q: str, type: str | None = "all", limit: int = 20, db: Session = Depends(get_db)
) -> dict:
    """
    Search across documents and conversations.

    Supports full-text search with optional type filtering.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=422, detail="Query parameter 'q' is required")

    if type not in ["all", "documents", "conversations"]:
        raise HTTPException(
            status_code=422,
            detail="Type must be 'all', 'documents', or 'conversations'",
        )

    try:
        rag_service = get_rag_service()

        # For now, focus on document search via RAG
        # In a full implementation, this would also search conversations
        if type in ["all", "documents"]:
            results = await rag_service.search_relevant_chunks(
                query=q.strip(), limit=limit
            )

            return {"query": q.strip(), "results": results, "total": len(results)}
        else:
            # Placeholder for conversation search
            return {
                "query": q.strip(),
                "results": [],
                "total": 0,
                "note": "Conversation search not yet implemented",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
