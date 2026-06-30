"""Camera start / stop / status / MJPEG stream endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.core.auth import verify_token
from backend.app.models.schemas import CameraStartRequest, error_response, success_response
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


@router.get("/camera/stream")
def stream_camera() -> StreamingResponse:
    """MJPEG live stream. No auth required (used in <img> tag)."""
    return StreamingResponse(
        camera_service.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
