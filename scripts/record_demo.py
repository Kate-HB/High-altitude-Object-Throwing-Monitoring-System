"""Record demo video: run full pipeline on a test video and collect outputs.

Produces a result video with annotations (detection boxes, tracks, ROI, events)
suitable for the 7/3 defense presentation. Also saves the first event snapshot
as a preview image.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2


def record_demo(
    video_path: str,
    output_dir: str = "outputs/demo",
    model_path: str = "models/best.pt",
    device: str = "0",
    roi: dict | None = None,
    threshold_preset: str = "default",
) -> Path:
    """Run pipeline and collect demo artifacts.

    Args:
        video_path: Source video file.
        output_dir: Output directory for result video + snapshots.
        model_path: YOLO model weights.
        device: CUDA device string.
        roi: ROI dict {x,y,width,height}, default covers full frame.
        threshold_preset: "default" | "sensitive" | "strict".

    Returns:
        Path to result video.
    """
    # ── Threshold presets ──
    presets = {
        "default": {
            "detect_confidence": 0.35,
            "downward_ratio": 0.55,
            "min_vertical_distance": 50,
            "min_track_frames": 5,
            "roi_required_ratio": 0.5,
            "alarm_cooldown_seconds": 10,
            "imgsz": 960,
        },
        "sensitive": {
            "detect_confidence": 0.25,
            "downward_ratio": 0.40,
            "min_vertical_distance": 30,
            "min_track_frames": 3,
            "roi_required_ratio": 0.3,
            "alarm_cooldown_seconds": 5,
            "imgsz": 960,
        },
        "strict": {
            "detect_confidence": 0.50,
            "downward_ratio": 0.65,
            "min_vertical_distance": 80,
            "min_track_frames": 8,
            "roi_required_ratio": 0.7,
            "alarm_cooldown_seconds": 20,
            "imgsz": 960,
        },
    }

    settings = presets.get(threshold_preset, presets["default"])

    video_path = Path(video_path)
    if not video_path.is_file():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Detect ROI from first frame if not specified ──
    cap = cv2.VideoCapture(str(video_path))
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    if roi is None:
        # Default: bottom 60% of frame (where falling objects appear)
        roi = {
            "x": 0,
            "y": int(frame_h * 0.4),
            "width": frame_w,
            "height": int(frame_h * 0.6),
        }

    print(f"Demo Configuration:")
    print(f"  Video: {video_path} ({frame_w}x{frame_h})")
    print(f"  ROI: {roi}")
    print(f"  Preset: {threshold_preset}")
    print(f"  Model: {model_path}")
    print(f"  Device: {device}")
    print(f"  Output: {out_dir}")

    # ── Run pipeline (import avoids subprocess overhead for direct usage) ──
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from algorithm.pipeline import run_video_analysis

    result = run_video_analysis(
        video_path=str(video_path),
        output_dir=str(out_dir),
        roi=roi,
        settings=settings,
        model_path=model_path,
        device=device,
    )

    # ── Write result summary ──
    summary = {
        "video": str(video_path),
        "preset": threshold_preset,
        "roi": roi,
        "result": {
            "status": result.status,
            "total_frames": result.total_frames,
            "processed_frames": result.processed_frames,
            "event_count": len(result.events),
            "result_video": result.result_video_path,
        },
    }

    summary_path = out_dir / "demo_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"\n{'='*50}")
    print(f"Status:       {result.status}")
    print(f"Frames:       {result.processed_frames}/{result.total_frames}")
    print(f"Events:       {len(result.events)}")
    print(f"Result Video: {result.result_video_path}")
    print(f"Summary:      {summary_path}")

    if result.events:
        print(f"\nEvent details:")
        for ev in result.events:
            print(f"  Track #{ev.get('track_id')}: "
                  f"frame={ev.get('trigger_frame')}, "
                  f"slope={ev.get('slope', 0):.4f}, "
                  f"snapshot={ev.get('snapshot_path', 'N/A')}")

    if result.error_message:
        print(f"\nERROR: {result.error_message}")
        sys.exit(1)

    return Path(result.result_video_path) if result.result_video_path else out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Record demo video with full pipeline")
    parser.add_argument("--video", required=True, help="Source video path")
    parser.add_argument("--output", default="outputs/demo", help="Output directory")
    parser.add_argument("--model", default="models/best.pt", help="Model path")
    parser.add_argument("--device", default="0", help="CUDA device")
    parser.add_argument("--preset", default="default",
                        choices=["default", "sensitive", "strict"],
                        help="Threshold preset")
    parser.add_argument("--roi", default=None,
                        help="ROI as JSON: {\"x\":0,\"y\":200,\"width\":640,\"height\":280}")
    args = parser.parse_args()

    roi = json.loads(args.roi) if args.roi else None

    try:
        record_demo(
            video_path=args.video,
            output_dir=args.output,
            model_path=args.model,
            device=args.device,
            roi=roi,
            threshold_preset=args.preset,
        )
    except Exception as exc:
        print(f"Demo recording failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
