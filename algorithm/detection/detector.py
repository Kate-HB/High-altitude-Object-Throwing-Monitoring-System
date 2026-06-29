"""YOLOv11 detector wrapper for falling_object detection.

Returns DetectionInfo dicts per docs/algorithm-interface.md Section 4.4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from ultralytics import YOLO

CLASS_NAME = "falling_object"


class Detector:
    """Thin wrapper around YOLOv11 inference.

    Usage:
        det = Detector("models/best.pt", conf=0.35, device="0")
        detections = det.predict_frame(frame)  # list[dict]
    """

    def __init__(self, model_path: str, conf: float = 0.35, device: str = "0") -> None:
        if not Path(model_path).exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        self.model = YOLO(model_path)
        self.conf = conf
        self.device = device

    def predict_frame(self, frame: np.ndarray, frame_id: int) -> list[dict[str, Any]]:
        """Run detection on a single frame, return DetectionInfo list.

        Each dict has: frame_id, bbox_x, bbox_y, bbox_width, bbox_height,
        confidence, class_name.
        """
        results = self.model.predict(frame, conf=self.conf, device=self.device, verbose=False, stream=False)
        detections: list[dict[str, Any]] = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "frame_id": frame_id,
                    "bbox_x": float(x1),
                    "bbox_y": float(y1),
                    "bbox_width": float(x2 - x1),
                    "bbox_height": float(y2 - y1),
                    "confidence": float(box.conf[0]),
                    "class_name": CLASS_NAME,
                })
        return detections

    def predict_video(self, video_path: str, conf: float | None = None) -> Any:
        """Run detection on entire video, return ultralytics results generator.

        Use stream=True for memory-efficient frame-by-frame iteration.
        """
        return self.model.predict(
            source=video_path,
            conf=conf or self.conf,
            device=self.device,
            stream=True,
            verbose=False,
        )
