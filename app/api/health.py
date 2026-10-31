"""Health check API router."""

from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Return service health status and timestamp."""
    return {
        "status": "healthy",
        "service": "ground-truth-ec",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }

