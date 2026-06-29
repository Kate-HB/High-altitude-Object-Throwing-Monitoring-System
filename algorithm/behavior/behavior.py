"""Behavior analyzer — 6-parameter trajectory rule with alarm cooldown.

Outputs EventInfo dicts per docs/algorithm-interface.md Section 4.3.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _point_in_roi(cx: float, cy: float, roi: dict[str, int]) -> bool:
    """Check if a center point falls inside the ROI rectangle."""
    return (
        roi["x"] <= cx <= roi["x"] + roi["width"]
        and roi["y"] <= cy <= roi["y"] + roi["height"]
    )


class BehaviorAnalyzer:
    """6-condition trajectory evaluator with per-track cooldown.

    Usage:
        ba = BehaviorAnalyzer()
        event = ba.evaluate(track_id, trajectory, confidences, timestamp, roi, settings)
        if event:
            save_snapshot(event["snapshot_path"])
    """

    def __init__(self) -> None:
        self._last_alarm: dict[int, float] = {}  # track_id -> last alarm timestamp (seconds)

    def evaluate(
        self,
        track_id: int,
        trajectory: list[tuple[int, float, float, float]],  # (frame_id, cx, cy, timestamp)
        confidences: list[float],
        current_timestamp: float,
        roi: dict[str, int],
        settings: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Check 6 conditions. Return EventInfo dict if all pass, else None.

        EventInfo fields: track_id, confidence, snapshot_path, created_at.
        """
        if not trajectory:
            return None

        # ── Read settings with defaults ──
        downward_ratio_thresh = float(settings.get("downward_ratio", 0.7))
        min_vertical_distance = int(settings.get("min_vertical_distance", 80))
        min_track_frames = int(settings.get("min_track_frames", 5))
        roi_required_ratio = float(settings.get("roi_required_ratio", 0.7))
        cooldown = float(settings.get("alarm_cooldown_seconds", 10))

        total = len(trajectory)

        # ── Condition 4: min track frames ──
        if total < min_track_frames:
            return None

        # ── Condition 2: downward trend (linear regression slope) ──
        # In image coords, y increases downward.
        # Use linear regression on trajectory to determine trend direction,
        # robust against frame-to-frame detection noise.
        n = total
        ts = [p[3] for p in trajectory]  # timestamps
        ys = [p[2] for p in trajectory]  # center_y
        mean_t = sum(ts) / n
        mean_y = sum(ys) / n
        num = sum((ts[i] - mean_t) * (ys[i] - mean_y) for i in range(n))
        den = sum((ts[i] - mean_t) ** 2 for i in range(n))
        slope = num / den if den > 1e-9 else 0.0  # dy/dt, positive = downward
        if slope <= 0:
            return None

        # ── Condition 3: min vertical distance ──
        vertical_dist = max(ys) - min(ys)
        if vertical_dist < min_vertical_distance:
            return None

        # ── Condition 5: ROI point ratio ──
        in_roi = sum(1 for p in trajectory if _point_in_roi(p[1], p[2], roi))
        roi_ratio = in_roi / total
        if roi_ratio < roi_required_ratio:
            return None

        # ── Condition 6: alarm cooldown ──
        last = self._last_alarm.get(track_id, -9999.0)
        if current_timestamp - last < cooldown:
            return None

        # ── All 6 passed → trigger ──
        self._last_alarm[track_id] = current_timestamp

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "track_id": track_id,
            "confidence": round(float(avg_conf), 4),
            "snapshot_path": "",  # filled by pipeline (needs output_dir)
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
