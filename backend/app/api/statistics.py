"""Statistics overview endpoint for the dashboard."""

from fastapi import APIRouter, Depends

from backend.app.core.auth import verify_token
from backend.app.models.schemas import error_response, success_response
from backend.app.services.statistics_service import get_overview

router = APIRouter(tags=["statistics"])


@router.get("/statistics/overview")
def query_overview(_auth: dict = Depends(verify_token)) -> dict:
    """Return 6-part dashboard statistics."""
    try:
        data = get_overview()
        return success_response(data)
    except Exception as exc:
        return error_response(500, "统计查询失败", str(exc))
