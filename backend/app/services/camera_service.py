"""OpenCV camera management — start, stop, status, MJPEG frame generator."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Generator

import cv2
import numpy as np

from backend.app.services.camera_ai import CameraAISession
from backend.app.services.event_service import (
    batch_insert_detections,
    batch_insert_events,
    batch_insert_tracks,
)
from backend.app.services.task_service import create_task, update_task

logger = logging.getLogger("backend.camera_service")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_camera: cv2.VideoCapture | None = None
_camera_lock = threading.Lock()
_camera_index: int = 0
_camera_width: int = 1280
_camera_height: int = 720
_camera_running: bool = False
_last_frame: np.ndarray | None = None
_last_frame_lock = threading.Lock()

# ── AI session state ──
_ai_session: CameraAISession | None = None
_ai_enabled: bool = False
_ai_task_id: int | None = None
_ai_events_lock = threading.Lock()
_ai_latest_events: list[dict[str, Any]] = []  # bounded ring buffer for polling


def start(camera_index: int = 0, width: int = 1280, height: int = 720) -> dict:
    """Start the camera capture thread. Returns status dict."""
    global _camera, _camera_index, _camera_width, _camera_height, _camera_running

    with _camera_lock:
        if _camera_running:
            return {"status": "already_running", "camera_index": _camera_index}

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            cap.release()
            return {"status": "error", "message": f"无法打开摄像头 index={camera_index}"}

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        _camera = cap
        _camera_index = camera_index
        _camera_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        _camera_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        _camera_running = True

        thread = threading.Thread(target=_capture_loop, daemon=True)
        thread.start()
        return {"status": "started", "camera_index": camera_index, "width": width, "height": height}


def stop() -> dict:
    """Stop the camera capture thread. Stops AI first if running. Returns status dict."""
    global _camera, _camera_running

    # Stop AI first to finalize task and persist events
    if _ai_enabled:
        stop_ai()

    with _camera_lock:
        if not _camera_running:
            return {"status": "not_running"}

        _camera_running = False
        # Give the capture loop a moment to exit
        time.sleep(0.2)
        if _camera is not None:
            _camera.release()
            _camera = None
        return {"status": "stopped"}


def get_status() -> dict:
    """Return current camera status."""
    with _camera_lock:
        if not _camera_running:
            return {
                "status": "offline",
                "camera_index": _camera_index,
                "width": _camera_width,
                "height": _camera_height,
            }
        return {
            "status": "online",
            "camera_index": _camera_index,
            "width": _camera_width,
            "height": _camera_height,
        }


def start_ai(roi: dict[str, int], settings: dict[str, Any] | None = None) -> dict:
    """Start AI processing on the live camera feed.

    Creates a video_tasks row for this session, initializes CameraAISession,
    and enables per-frame processing in the capture loop.

    Args:
        roi: {"x", "y", "width", "height"} in pixels.
        settings: Detection/tracking params. Uses DB defaults if None.

    Returns:
        {"status": "ai_started", "task_id": int} or {"status": "error", "message": str}
    """
    global _ai_session, _ai_enabled, _ai_task_id, _ai_latest_events

    if _ai_enabled:
        return {"status": "error", "message": "AI已在运行中"}

    if not _camera_running:
        return {"status": "error", "message": "摄像头未启动，请先开启摄像头"}

    # Load settings from DB if not provided
    if settings is None:
        try:
            from backend.app.services.settings_service import get_settings
            db_settings = get_settings()
            # system_settings is flat: {detect_confidence, downward_ratio, ...}
            # Remove id/updated_at, keep only algorithm params
            settings = {
                k: v for k, v in db_settings.items()
                if k not in ("id", "updated_at") and v is not None
            }
        except Exception:
            settings = {}

    # Set defaults for any missing keys
    defaults = {"detect_confidence": 0.35}
    for k, v in defaults.items():
        settings.setdefault(k, v)

    model_path = str(_PROJECT_ROOT / "models" / "best.onnx")
    if not Path(model_path).is_file():
        return {"status": "error", "message": f"模型文件不存在: {model_path}"}

    # Create a video_tasks row for this camera session
    try:
        task_id = create_task(
            source_type="camera",
            source_path=f"camera://{_camera_index}",
            total_frames=0,
            roi=roi,
        )
    except Exception as e:
        return {"status": "error", "message": f"创建任务记录失败: {e}"}

    output_dir = f"outputs/task_{task_id}"

    try:
        session = CameraAISession(
            model_path=model_path,
            roi=roi,
            settings=settings,
            device="0",
            output_dir=output_dir,
            snapshots_dir=str(_PROJECT_ROOT / "events" / "snapshots"),
        )
    except FileNotFoundError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.exception("Failed to initialize CameraAISession")
        return {"status": "error", "message": f"AI初始化失败: {e}"}

    _ai_session = session
    _ai_task_id = task_id
    _ai_latest_events = []
    _ai_enabled = True

    logger.info("Camera AI started: task_id=%d, roi=%s", task_id, roi)
    return {"status": "ai_started", "task_id": task_id}


def stop_ai() -> dict:
    """Stop AI processing. Camera keeps running. Persists accumulated data."""
    global _ai_session, _ai_enabled, _ai_task_id, _ai_latest_events

    if not _ai_enabled:
        return {"status": "error", "message": "AI未在运行"}

    _ai_enabled = False
    session = _ai_session
    task_id = _ai_task_id

    event_count = 0
    det_count = 0
    trk_count = 0

    if session is not None and task_id is not None:
        try:
            # Batch insert accumulated detections and tracks
            # Events are already persisted in real-time during capture
            det_count = batch_insert_detections(task_id, session.detection_results)
            trk_count = batch_insert_tracks(task_id, session.tracking_results)
        except Exception:
            logger.exception("Failed to persist camera AI results for task %d", task_id)

        result_video = session.close()

        try:
            update_task(
                task_id,
                status="success",
                processed_frames=session.frame_count,
                result_video_path=result_video,
            )
        except Exception:
            logger.exception("Failed to update camera task %d", task_id)

        event_count = session.total_events

    _ai_session = None
    _ai_task_id = None
    _ai_latest_events = []

    logger.info(
        "Camera AI stopped: task_id=%d, events=%d, detections=%d, tracks=%d",
        task_id, event_count, det_count, trk_count,
    )
    return {
        "status": "ai_stopped",
        "task_id": task_id,
        "events": event_count,
        "detections": det_count,
        "tracks": trk_count,
    }


def get_ai_status() -> dict:
    """Return current AI processing status."""
    if not _ai_enabled or _ai_session is None:
        return {
            "ai_enabled": False,
            "task_id": None,
            "frame_count": 0,
            "active_tracks": 0,
            "total_events": 0,
            "latest_events": [],
        }

    session = _ai_session
    with _ai_events_lock:
        latest = list(_ai_latest_events[-20:])

    return {
        "ai_enabled": True,
        "task_id": _ai_task_id,
        "frame_count": session.frame_count,
        "active_tracks": session.active_track_count,
        "total_events": session.total_events,
        "latest_events": latest,
    }


def generate_frames() -> Generator[bytes, None, None]:
    """Generator yielding MJPEG frames for StreamingResponse."""
    global _last_frame

    while _camera_running:
        with _last_frame_lock:
            if _last_frame is None:
                time.sleep(0.03)
                continue
            frame = _last_frame.copy()

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )
        time.sleep(0.03)  # ~30 fps


def _capture_loop() -> None:
    """Background thread: continuously read frames from camera."""
    global _camera, _camera_running, _last_frame
    global _ai_enabled, _ai_session, _ai_task_id, _ai_latest_events

    while _camera_running:
        with _camera_lock:
            if _camera is None or not _camera_running:
                break
            ret, frame = _camera.read()

        if not ret:
            time.sleep(0.05)
            continue

        # AI processing (in capture thread — sequential, GPU-bound)
        if _ai_enabled and _ai_session is not None:
            try:
                annotated, new_events = _ai_session.process_frame(frame)
                with _last_frame_lock:
                    _last_frame = annotated
                if new_events:
                    with _ai_events_lock:
                        _ai_latest_events.extend(new_events)
                        if len(_ai_latest_events) > 100:
                            _ai_latest_events = _ai_latest_events[-100:]
                    # Immediately persist events to DB (with snapshot_path already set)
                    try:
                        batch_insert_events(_ai_task_id, new_events)
                    except Exception:
                        logger.exception("Failed to persist camera events to DB")
            except Exception:
                logger.exception("Camera AI process_frame failed")
                # Continue with raw frame on error
                with _last_frame_lock:
                    _last_frame = frame
        else:
            with _last_frame_lock:
                _last_frame = frame
