"""Camera start / stop / status / MJPEG stream endpoints."""

import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.core.auth import verify_token
from backend.app.models.schemas import CameraAIStartRequest, CameraStartRequest, error_response, success_response
from backend.app.services import camera_service

router = APIRouter(tags=["camera"])


@router.post("/camera/start")
def start_camera(body: CameraStartRequest, _auth: dict = Depends(verify_token)) -> dict:
    """Start the camera capture. Returns 200 on success, 503 if camera unavailable."""
    result = camera_service.start(
        camera_index=body.camera_index, width=body.width, height=body.height
    )
    if result.get("status") == "error":
        return error_response(503, "摄像头不可用", result.get("message", ""))
    return success_response(result, message="摄像头已启动")


@router.post("/camera/stop")
def stop_camera(_auth: dict = Depends(verify_token)) -> dict:
    """Stop the camera capture."""
    result = camera_service.stop()
    return success_response(result, message="摄像头已停止")


@router.get("/camera/status")
def query_camera_status(_auth: dict = Depends(verify_token)) -> dict:
    """Return current camera status."""
    result = camera_service.get_status()
    return success_response(result)


@router.get("/camera/status/stream")
def stream_camera_status() -> StreamingResponse:
    """SSE stream for camera status — push updates every 3 seconds. No auth."""
    def generate():
        while True:
            status = camera_service.get_status()
            yield f"data: {json.dumps(status)}\n\n"
            time.sleep(3)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/camera/stream")
def stream_camera() -> StreamingResponse:
    """MJPEG live stream. No auth required (used in <img> tag)."""
    return StreamingResponse(
        camera_service.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/camera/ai/start")
def start_camera_ai(
    body: CameraAIStartRequest,
    _auth: dict = Depends(verify_token),
) -> dict:
    """Start AI processing on the live camera feed."""
    roi = {
        "x": body.roi_x,
        "y": body.roi_y,
        "width": body.roi_width or 0,
        "height": body.roi_height or 0,
    }
    settings_override = {}
    if body.detect_confidence is not None:
        settings_override["detect_confidence"] = body.detect_confidence

    result = camera_service.start_ai(roi, settings_override or None)
    if result.get("status") == "error":
        return error_response(400, "AI启动失败", result.get("message", ""))
    return success_response(result, message="AI处理已启动")


@router.post("/camera/ai/stop")
def stop_camera_ai(
    _auth: dict = Depends(verify_token),
) -> dict:
    """Stop AI processing. Camera keeps running."""
    result = camera_service.stop_ai()
    if result.get("status") == "error":
        return error_response(400, "AI停止失败", result.get("message", ""))
    return success_response(result, message="AI处理已停止")


@router.get("/camera/ai/status")
def query_camera_ai_status(
    _auth: dict = Depends(verify_token),
) -> dict:
    """Return AI processing status with latest events."""
    result = camera_service.get_ai_status()
    return success_response(result)
