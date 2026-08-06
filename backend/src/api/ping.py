"""
Simple ping endpoint for health checks and automation
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/ping")
async def ping() -> dict:
    """Simple ping endpoint that returns pong."""
    return {"status": "pong", "service": "tcyberchat"}
