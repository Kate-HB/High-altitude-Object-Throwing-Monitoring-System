"""Health check endpoint — no auth required."""

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.models.schemas import now_str, success_response

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return success_response(
        {
            "status": "running",
            "service": settings.app_name,
            "version": settings.app_version,
            "time": now_str(),
        }
    )
