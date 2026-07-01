"""Algorithm pipeline interface.

This module defines the contract between backend and algorithm.
The function signature and PipelineResult structure are FROZEN —
changes must be approved by 罗龙飞 and synced to docs/algorithm-interface.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

from algorithm.behavior.behavior import BehaviorAnalyzer
from algorithm.tracking.tracker import DeepSORTTracker


@dataclass
class PipelineResult:
    """Result returned by run_video_analysis().

    Field definitions: docs/algorithm-interface.md Section 4.
    """

    status: str  # "success" | "failed"
    total_frames: int = 0
    processed_frames: int = 0
    result_video_path: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    detection_results: list[dict[str, Any]] = field(default_factory=list)
    tracking_results: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None


def run_video_analysis(
    video_path: str,
    output_dir: str,
    roi: dict[str, int],
    settings: dict[str, Any],
    *,
    model_path: str = "models/best.onnx",
    #yolo11s_v1.onnx，best.onnx
    device: str = "0",
) -> PipelineResult:
    """Run the full detection-tracking-behavior pipeline on a video.

    Args:
        video_path: Path to source video file.
        output_dir: Directory for result video and snapshots.
        roi: {"x": int, "y": int, "width": int, "height": int}.
        settings: Detection and alarm parameters
            (detect_confidence, downward_ratio, min_vertical_distance,
             min_track_frames, roi_required_ratio, alarm_cooldown_seconds).
        model_path: Path to YOLO model weights.
        device: CUDA device string or "cpu".

    Returns:
        PipelineResult with status, frames, events, detections, tracks.
    """
    # ── Guards ──
    if not Path(video_path).is_file():
        return PipelineResult(status="failed", error_message="视频文件不存在")
    if not Path(model_path).is_file():
        return PipelineResult(status="failed", error_message="模型文件不存在")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return PipelineResult(status="failed", error_message="视频读取失败")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    # ── Normalize ROI (handle None values from API) ──
    roi = {
        "x": int(roi.get("x") or 0),
        "y": int(roi.get("y") or 0),
        "width": int(roi.get("width") or 0),
        "height": int(roi.get("height") or 0),
    }

    # ── Init modules ──
    try:
        conf = float(settings.get("detect_confidence", 0.35))
    except (TypeError, ValueError):
        conf = 0.35

    try:
        imgsz = int(settings.get("imgsz", 960))
    except (TypeError, ValueError):
        imgsz = 960

    from algorithm.detection.detector import Detector  # lazy import (needs ultralytics)

    try:
        detector = Detector(model_path, conf=conf, device=device, imgsz=imgsz)
    except Exception as exc:
        cap.release()
        return PipelineResult(status="failed", error_message=f"模型加载失败: {exc}")

    tracker = DeepSORTTracker()
    behavior = BehaviorAnalyzer()

    # ── Output dirs ──
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snap_dir = out_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "result.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"H264")
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(result_path), cv2.CAP_MSMF, fourcc, fps, (frame_w, frame_h))

    # Progress file for real-time polling
    progress_file = out_dir / "progress.json"
    events_live_file = out_dir / "events_live.json"

    def _write_progress(fid: int, ev_count: int) -> None:
        try:
            progress_file.write_text(json.dumps(
                {"frame": fid, "total": total_frames, "events": ev_count},
                ensure_ascii=False,
            ))
        except Exception:
            pass  # best-effort, don't fail the pipeline

    def _write_events_live() -> None:
        """Write accumulated events so the frontend can poll them during analysis."""
        try:
            events_live_file.write_text(json.dumps(
                events, ensure_ascii=False,
            ))
        except Exception:
            pass

    # ── Accumulators ──
    detection_results: list[dict[str, Any]] = []
    tracking_results: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    frame_id = 0
    processed = 0
    track_colors: dict[int, tuple[int, int, int]] = {}

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_id += 1
            timestamp = float(frame_id) / fps

            # ── 1. Detection ──
            dets = detector.predict_frame(frame, frame_id)
            # ROI filter: keep only detections whose center falls inside ROI
            if roi["width"] > 0 and roi["height"] > 0:
                dets = [
                    d for d in dets
                    if roi["x"] <= d["bbox_x"] + d["bbox_width"] / 2 <= roi["x"] + roi["width"]
                    and roi["y"] <= d["bbox_y"] + d["bbox_height"] / 2 <= roi["y"] + roi["height"]
                ]
            detection_results.extend(dets)

            # ── 2. Tracking ──
            trks = tracker.update(dets, frame_id, timestamp)
            tracking_results.extend(trks)

            # ── 3. Behavior evaluation ──
            # Collect triggered tracks first, draw later so snapshots have annotations
            triggered: list[tuple[int, dict[str, Any]]] = []
            for tid in tracker.active_track_ids:
                t = tracker.tracks[tid]
                event = behavior.evaluate(
                    track_id=tid,
                    trajectory=t["trajectory"],
                    confidences=t["confidences"],
                    current_timestamp=timestamp,
                    roi=roi,
                    settings=settings,
                )
                if event is not None:
                    triggered.append((tid, event))

            # ── 4. Draw result frame ──
            # ROI rectangle
            cv2.rectangle(
                frame,
                (roi["x"], roi["y"]),
                (roi["x"] + roi["width"], roi["y"] + roi["height"]),
                (255, 0, 0),
                2,
            )

            # Detection boxes
            for d in dets:
                x1, y1 = int(d["bbox_x"]), int(d["bbox_y"])
                x2, y2 = x1 + int(d["bbox_width"]), y1 + int(d["bbox_height"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Trajectories + track IDs (confirmed tracks only)
            for tid in tracker.active_track_ids:
                t = tracker.tracks[tid]
                if tid not in track_colors:
                    track_colors[tid] = (
                        (tid * 67 + 50) % 256,
                        (tid * 137 + 80) % 256,
                        (tid * 193 + 120) % 256,
                    )
                color = track_colors[tid]

                # Trajectory line
                pts = [(int(p[1]), int(p[2])) for p in t["trajectory"]]
                for i in range(1, len(pts)):
                    cv2.line(frame, pts[i - 1], pts[i], color, 2)

                # Track ID label at last known center
                cx, cy = t["center"]
                cv2.putText(frame, f"ID:{tid}", (int(cx) + 5, int(cy) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Save annotated snapshots for triggered tracks
            for tid, event in triggered:
                snap_name = f"event_{tid}_{frame_id:06d}.jpg"
                snap_path = snap_dir / snap_name
                # Highlight the triggering track with a thicker red box
                t = tracker.tracks[tid]
                bx, by = t["bbox"][:2]
                bw, bh = t["bbox"][2] - bx, t["bbox"][3] - by
                cv2.rectangle(frame, (int(bx), int(by)), (int(bx + bw), int(by + bh)),
                              (0, 0, 255), 3)
                cv2.putText(frame, f"EVENT ID:{tid}", (int(bx), int(by) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.imwrite(str(snap_path), frame)
                event["snapshot_path"] = str(snap_path)
                events.append(event)
                _write_events_live()

            writer.write(frame)
            processed += 1
            _write_progress(frame_id, len(events))

    except Exception as exc:
        cap.release()
        writer.release()
        return PipelineResult(status="failed", error_message=f"算法处理异常: {exc}")
    finally:
        cap.release()
        writer.release()

    return PipelineResult(
        status="success",
        total_frames=total_frames,
        processed_frames=processed,
        result_video_path=str(result_path.as_posix()),
        events=events,
        detection_results=detection_results,
        tracking_results=tracking_results,
    )
