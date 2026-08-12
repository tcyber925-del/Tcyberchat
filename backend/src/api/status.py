"""
Simple API status endpoint for automation tooling
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/status")
async def status() -> dict:
    """Return API status information for automation tooling."""
    return {"status": "running", "service": "tcyberchat", "version": "1.0.0"}
