"""Event list, detail, and status-update endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.auth import verify_token
from backend.app.models.schemas import (
    EventStatusUpdate,
    error_response,
    success_response,
)
from backend.app.services.event_service import (
    get_event,
    list_events,
    update_event_status,
)

router = APIRouter(tags=["events"])


@router.get("/events")
def query_events(
    task_id: int | None = Query(None, description="Filter by video task id"),
    status: str | None = Query(None, description="Filter by event status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _auth: dict = Depends(verify_token),
) -> dict:
    """List events with optional task/status filters."""
    events = list_events(task_id=task_id, status=status, limit=limit, offset=offset)
    return success_response({"events": events, "count": len(events)})


@router.get("/events/{event_id}")
def query_event(
    event_id: int,
    _auth: dict = Depends(verify_token),
) -> dict:
    """Get a single event with its detections and tracks."""
    event = get_event(event_id)
    if event is None:
        return error_response(404, "事件不存在", f"event_id={event_id} 未找到")
    return success_response(event)


@router.patch("/events/{event_id}/status")
def patch_event_status(
    event_id: int,
    body: EventStatusUpdate,
    _auth: dict = Depends(verify_token),
) -> dict:
    """Update an event's confirmation status."""
    if body.status not in ("unconfirmed", "confirmed", "false_alarm"):
        return error_response(400, "无效状态值", f"status={body.status}")

    event = get_event(event_id)
    if event is None:
        return error_response(404, "事件不存在", f"event_id={event_id} 未找到")

    ok = update_event_status(event_id, body.status)
    if not ok:
        return error_response(500, "更新失败", "数据库未响应")
    return success_response({"event_id": event_id, "status": body.status}, message="状态已更新")
