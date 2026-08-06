"""
Simple liveness health check endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Simple liveness probe that always returns ok."""
    return {"status": "ok", "version": "1.0.0"}
