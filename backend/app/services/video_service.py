"""Video file save and metadata extraction."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile


ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
UPLOAD_DIR = Path("uploads")


def _validate_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"不支持的文件格式: {suffix}，仅支持 {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )


async def save_upload(file: UploadFile) -> dict:
    """Save uploaded video to uploads/ with a UUID-prefixed name.

    Returns:
        dict with keys: filename, filepath, size
    """
    original = file.filename or "video.mp4"
    _validate_extension(original)
    unique_name = f"{uuid.uuid4().hex}_{original}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / unique_name

    content = await file.read()
    dest.write_bytes(content)

    return {
        "filename": unique_name,
        "filepath": str(dest),
        "size": len(content),
    }


def get_total_frames(filepath: str) -> int:
    """Read total frame count using OpenCV."""
    import cv2

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"无法打开视频文件: {filepath}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total
