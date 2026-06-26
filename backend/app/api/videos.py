"""Video upload, analysis start, and task progress endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, Form

from backend.app.core.auth import verify_token
from backend.app.models.schemas import (
    ROIRequest,
    error_response,
    success_response,
)
from backend.app.services.settings_service import get_settings
from backend.app.services.task_service import create_task, get_task, start_analysis
from backend.app.services.video_service import get_total_frames, save_upload

router = APIRouter(tags=["videos"])


@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    roi_x: int = Form(0),
    roi_y: int = Form(0),
    roi_width: int | None = Form(None),
    roi_height: int | None = Form(None),
    _auth: dict = Depends(verify_token),
) -> dict:
    """Upload a video file, create a task record, return task_id."""
    try:
        saved = await save_upload(file)
    except ValueError as e:
        return error_response(415, "不支持的文件格式", str(e))

    try:
        total_frames = get_total_frames(saved["filepath"])
    except RuntimeError as e:
        return error_response(400, "无法读取视频", str(e))

    roi = {"x": roi_x, "y": roi_y, "width": roi_width, "height": roi_height}
    task_id = create_task(
        source_type="upload",
        source_path=saved["filepath"],
        total_frames=total_frames,
        roi=roi,
    )

    return success_response(
        {
            "task_id": task_id,
            "filename": saved["filename"],
            "size": saved["size"],
            "total_frames": total_frames,
        },
        message="上传成功",
    )


@router.post("/tasks/{task_id}/analyze")
def analyze_task(
    task_id: int,
    body: ROIRequest,
    _auth: dict = Depends(verify_token),
) -> dict:
    """Submit ROI and start background analysis."""
    task = get_task(task_id)
    if task is None:
        return error_response(404, "任务不存在", f"task_id={task_id} 未找到")

    if task["status"] != "pending":
        return error_response(409, "任务状态不允许分析", f"当前状态: {task['status']}")

    roi = {
        "x": body.roi_x,
        "y": body.roi_y,
        "width": body.roi_width,
        "height": body.roi_height,
    }
    settings = get_settings()
    settings.pop("id", None)
    settings.pop("updated_at", None)

    start_analysis(task_id, roi, settings)

    return success_response(
        {"task_id": task_id, "status": "running"}, message="分析已启动"
    )


@router.get("/tasks/{task_id}")
def query_task(
    task_id: int,
    _auth: dict = Depends(verify_token),
) -> dict:
    """Query task progress and related events."""
    task = get_task(task_id)
    if task is None:
        return error_response(404, "任务不存在", f"task_id={task_id} 未找到")

    return success_response(task)
