"""Real-time AI processing session for live camera feed.

Wraps the existing algorithm modules (Detector, DeepSORTTracker, BehaviorAnalyzer)
for per-frame processing. Records annotated frames to result video and saves
event snapshots inline.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from algorithm.behavior.behavior import BehaviorAnalyzer
from algorithm.detection.detector import Detector
from algorithm.tracking.tracker import DeepSORTTracker


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class CameraAISession:
    """Stateful AI session for real-time camera processing.

    One instance per camera session. Holds Detector, DeepSORTTracker, and
    BehaviorAnalyzer instances that maintain state across frames.

    Usage:
        session = CameraAISession("models/best.pt", roi, settings)
        for frame in camera_frames:
            annotated, events = session.process_frame(frame)
            # stream annotated, save events to DB
    """

    def __init__(
        self,
        model_path: str,
        roi: dict[str, int],
        settings: dict[str, Any],
        device: str = "0",
        output_dir: str = "outputs/camera",
        snapshots_dir: str = "events/snapshots",
    ) -> None:
        if not Path(model_path).is_file():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        self.roi = {
            "x": int(roi.get("x") or 0),
            "y": int(roi.get("y") or 0),
            "width": int(roi.get("width") or 0),
            "height": int(roi.get("height") or 0),
        }
        self.settings = settings

        conf = float(settings.get("detect_confidence", 0.35))
        imgsz = int(settings.get("imgsz", 960))
        self.detector = Detector(model_path, conf=conf, device=device, imgsz=imgsz)
        self.tracker = DeepSORTTracker()
        self.behavior = BehaviorAnalyzer()

        self._out_dir = _PROJECT_ROOT / output_dir
        self._out_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots_dir = _PROJECT_ROOT / snapshots_dir
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

        # VideoWriter — lazy init on first frame (need frame dims)
        self._writer: cv2.VideoWriter | None = None
        self._result_path = self._out_dir / "result.mp4"
        self._rel_result_path = f"{output_dir}/result.mp4"
        self._fps = 30.0

        self._frame_count = 0
        self._total_events = 0
        self._start_time = time.time()
        self._track_colors: dict[int, tuple[int, int, int]] = {}

        # Accumulators for batch DB insert
        self.detection_results: list[dict[str, Any]] = []
        self.tracking_results: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []

    # ── Properties ──

    @property
    def active_track_count(self) -> int:
        return len(self.tracker.active_track_ids)

    @property
    def total_events(self) -> int:
        return self._total_events

    @property
    def frame_count(self) -> int:
        return self._frame_count

    # ── Core processing ──

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """Detect → track → behavior → annotate.

        Args:
            frame: BGR numpy array (H, W, 3).

        Returns:
            (annotated_frame, triggered_events) where annotated_frame is a
            BGR numpy array with drawn annotations, and triggered_events is
            a list of EventInfo dicts triggered on this frame.
        """
        self._frame_count += 1
        frame_id = self._frame_count
        timestamp = time.time() - self._start_time

        # ── 1. Detection ──
        dets = self.detector.predict_frame(frame, frame_id)

        # ROI filter: keep only detections whose center falls inside ROI
        r = self.roi
        if r["width"] > 0 and r["height"] > 0:
            dets = [
                d for d in dets
                if r["x"] <= d["bbox_x"] + d["bbox_width"] / 2 <= r["x"] + r["width"]
                and r["y"] <= d["bbox_y"] + d["bbox_height"] / 2 <= r["y"] + r["height"]
            ]
        self.detection_results.extend(dets)

        # ── 2. Tracking ──
        trks = self.tracker.update(dets, frame_id, timestamp)
        self.tracking_results.extend(trks)

        # ── 3. Behavior evaluation ──
        triggered: list[tuple[int, dict[str, Any]]] = []
        for tid in self.tracker.active_track_ids:
            t = self.tracker.tracks[tid]
            event = self.behavior.evaluate(
                track_id=tid,
                trajectory=t["trajectory"],
                confidences=t["confidences"],
                current_timestamp=timestamp,
                roi=self.roi,
                settings=self.settings,
            )
            if event is not None:
                triggered.append((tid, event))

        # ── 4. Draw annotations ──
        annotated = self._draw_frame(frame, dets, triggered)

        # ── 4a. Write to result video ──
        if self._writer is None:
            h, w = annotated.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"H264")
            self._writer = cv2.VideoWriter(
                str(self._result_path), cv2.CAP_MSMF, fourcc, self._fps, (w, h),
            )
        self._writer.write(annotated)

        # ── 5. Save snapshots for triggered events ──
        new_events: list[dict[str, Any]] = []
        for tid, event in triggered:
            snap_name = f"event_{tid}_{self._frame_count:06d}.jpg"
            snap_path = self._snapshots_dir / snap_name
            cv2.imwrite(str(snap_path), annotated)
            event["snapshot_path"] = f"events/snapshots/{snap_name}"
            new_events.append(event)
            self._total_events += 1

        self.events.extend(new_events)
        return annotated, new_events

    # ── Drawing ──

    def _draw_frame(
        self,
        frame: np.ndarray,
        dets: list[dict[str, Any]],
        triggered: list[tuple[int, dict[str, Any]]],
    ) -> np.ndarray:
        """Draw ROI, detection boxes, trajectories, track IDs, and event highlights."""
        r = self.roi

        # ROI rectangle (blue)
        if r["width"] > 0 and r["height"] > 0:
            cv2.rectangle(
                frame,
                (r["x"], r["y"]),
                (r["x"] + r["width"], r["y"] + r["height"]),
                (255, 0, 0),
                2,
            )

        # Detection boxes (green)
        for d in dets:
            x1, y1 = int(d["bbox_x"]), int(d["bbox_y"])
            x2, y2 = x1 + int(d["bbox_width"]), y1 + int(d["bbox_height"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Trajectories + track IDs (confirmed tracks only)
        for tid in self.tracker.active_track_ids:
            t = self.tracker.tracks[tid]
            if tid not in self._track_colors:
                self._track_colors[tid] = (
                    (tid * 67 + 50) % 256,
                    (tid * 137 + 80) % 256,
                    (tid * 193 + 120) % 256,
                )
            color = self._track_colors[tid]

            # Trajectory line
            pts = [(int(p[1]), int(p[2])) for p in t["trajectory"]]
            for i in range(1, len(pts)):
                cv2.line(frame, pts[i - 1], pts[i], color, 2)

            # Track ID label
            cx, cy = t["center"]
            cv2.putText(
                frame, f"ID:{tid}", (int(cx) + 5, int(cy) - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
            )

        # Event highlights (red thick box + label)
        triggered_ids = {tid for tid, _ in triggered}
        for tid in self.tracker.active_track_ids:
            if tid not in triggered_ids:
                continue
            t = self.tracker.tracks[tid]
            bx, by = t["bbox"][:2]
            bw, bh = t["bbox"][2] - bx, t["bbox"][3] - by
            cv2.rectangle(
                frame,
                (int(bx), int(by)),
                (int(bx + bw), int(by + bh)),
                (0, 0, 255),
                3,
            )
            cv2.putText(
                frame,
                f"EVENT ID:{tid}",
                (int(bx), int(by) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        return frame

    # ── Lifecycle ──

    def close(self) -> str:
        """Release VideoWriter and return result_video_path.

        Safe to call multiple times.
        """
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        return self._rel_result_path if self._result_path.exists() else ""

    def reset(self) -> None:
        """Reset tracker and behavior state, clear accumulators."""
        self.close()
        self.tracker = DeepSORTTracker()
        self.behavior = BehaviorAnalyzer()
        self._frame_count = 0
        self._total_events = 0
        self._start_time = time.time()
        self._track_colors.clear()
        self.detection_results.clear()
        self.tracking_results.clear()
        self.events.clear()
