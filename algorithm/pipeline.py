"""Algorithm pipeline interface.

This module defines the contract between backend and algorithm.
The function signature and PipelineResult structure are FROZEN —
changes must be approved by 罗龙飞 and synced to docs/algorithm-interface.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineResult:
    """Result returned by run_video_analysis().

    Field definitions: docs/algorithm-interface.md Section 4.
    """

    status: str  # "success" | "failed" | "not_ready"
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
) -> PipelineResult:
    """Run the full detection-tracking-behavior pipeline on a video.

    This is the single entry point the backend should call.
    Currently a PLACEHOLDER — always returns status="not_ready".

    Args:
        video_path: Path to source video file.
        output_dir: Directory for result video and snapshots.
        roi: {"x": int, "y": int, "width": int, "height": int}.
        settings: Detection and alarm parameters
            (detect_confidence, downward_ratio, min_vertical_distance,
             min_track_frames, roi_required_ratio, alarm_cooldown_seconds).

    Returns:
        PipelineResult with status, frames, events, detections, tracks.
    """
    return PipelineResult(
        status="not_ready",
        error_message="Detection model is not loaded",
    )
