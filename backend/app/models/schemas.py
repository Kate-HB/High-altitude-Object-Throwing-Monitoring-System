"""Pydantic request/response models and unified response helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Unified response helpers ──────────────────────────────────────────

def success_response(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 200, "message": message, "data": data}


def error_response(
    code: int, message: str, detail: str | dict[str, Any]
) -> dict[str, Any]:
    return {"code": code, "message": message, "detail": detail}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Request models ────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class ROIRequest(BaseModel):
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None
    detect_confidence: float = 0.35


class EventStatusUpdate(BaseModel):
    status: str  # unconfirmed / confirmed / false_alarm


class SettingsUpdate(BaseModel):
    detect_confidence: Optional[float] = None
    downward_ratio: Optional[float] = None
    min_vertical_distance: Optional[int] = None
    min_track_frames: Optional[int] = None
    roi_required_ratio: Optional[float] = None
    alarm_cooldown_seconds: Optional[int] = None
    imgsz: Optional[int] = None


class CameraStartRequest(BaseModel):
    camera_index: int = 0
    width: int = 1280
    height: int = 720


class CameraAIStartRequest(BaseModel):
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None
    detect_confidence: float | None = None
