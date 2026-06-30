"""OpenCV camera management — start, stop, status, MJPEG frame generator."""

from __future__ import annotations

import threading
import time
from typing import Generator

import cv2
import numpy as np

_camera: cv2.VideoCapture | None = None
_camera_lock = threading.Lock()
_camera_index: int = 0
_camera_running: bool = False
_last_frame: np.ndarray | None = None
_last_frame_lock = threading.Lock()


def start(camera_index: int = 0, width: int = 640, height: int = 480) -> dict:
    """Start the camera capture thread. Returns status dict."""
    global _camera, _camera_index, _camera_running

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
        _camera_running = True

        thread = threading.Thread(target=_capture_loop, daemon=True)
        thread.start()
        return {"status": "started", "camera_index": camera_index, "width": width, "height": height}


def stop() -> dict:
    """Stop the camera capture thread. Returns status dict."""
    global _camera, _camera_running

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
            return {"status": "offline", "camera_index": _camera_index}
        return {"status": "online", "camera_index": _camera_index}


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

    while _camera_running:
        with _camera_lock:
            if _camera is None or not _camera_running:
                break
            ret, frame = _camera.read()

        if ret:
            with _last_frame_lock:
                _last_frame = frame
        else:
            time.sleep(0.05)
