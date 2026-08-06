"""
Simple API version endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/version")
async def version() -> dict:
    """Return API version information for automation tooling."""
    return {"version": "1.0.0", "status": "ok"}
