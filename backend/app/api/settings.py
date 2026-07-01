"""System settings read/write endpoints."""

from fastapi import APIRouter, Depends

from backend.app.core.auth import verify_token
from backend.app.models.schemas import SettingsUpdate, error_response, success_response
from backend.app.services.settings_service import get_settings, update_settings

router = APIRouter(tags=["settings"])


@router.get("/settings")
def read_settings(_auth: dict = Depends(verify_token)) -> dict:
    """Read current system parameters."""
    try:
        data = get_settings()
        return success_response(data)
    except Exception as exc:
        return error_response(500, "参数读取失败", str(exc))


@router.put("/settings")
def write_settings(body: SettingsUpdate, _auth: dict = Depends(verify_token)) -> dict:
    """Update system parameters (partial update — only provided fields)."""
    try:
        # Only pass fields that are explicitly set (non-None for floats would be 0, so pass all)
        # SettingsUpdate requires all fields, so pass the whole model dump
        updated = update_settings(body.model_dump())
        return success_response(updated, message="参数已更新")
    except ValueError as exc:
        return error_response(400, "参数校验失败", str(exc))
    except Exception as exc:
        return error_response(500, "参数更新失败", str(exc))
