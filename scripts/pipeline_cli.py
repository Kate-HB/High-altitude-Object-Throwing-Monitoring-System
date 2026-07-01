"""CLI wrapper for algorithm pipeline — called by backend via subprocess.

Reads inputs as JSON args, outputs PipelineResult as JSON to stdout.
Uses Conda Python environment which has torch + ultralytics.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from io import StringIO
from pathlib import Path

# Suppress ultralytics logging noise
logging.getLogger("ultralytics").setLevel(logging.ERROR)
os.environ["ULTRALYTICS_VERBOSE"] = "False"

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run algorithm pipeline (JSON I/O)")
    parser.add_argument("--video", required=True, help="Source video path")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--roi", required=True, help="ROI as JSON: {x,y,width,height}")
    parser.add_argument("--settings", required=True, help="Settings as JSON")
    parser.add_argument("--model", default="models/best.onnx", help="Model weights path")
    parser.add_argument("--device", default="0", help="CUDA device")
    args = parser.parse_args()

    try:
        roi = json.loads(args.roi)
        settings = json.loads(args.settings)
    except json.JSONDecodeError as exc:
        result = {"status": "failed", "error_message": f"JSON参数解析失败: {exc}"}
        json.dump(result, sys.stdout, ensure_ascii=False, default=str)
        return

    # Import here so import-time prints are captured
    # Redirect stdout to suppress ultralytics ONNX loading messages
    _real_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        from algorithm.pipeline import run_video_analysis  # noqa: E402

        result = run_video_analysis(
            video_path=args.video,
            output_dir=args.output_dir,
            roi=roi,
            settings=settings,
            model_path=args.model,
            device=args.device,
        )
    finally:
        sys.stdout = _real_stdout

    # Output clean JSON to real stdout
    output = {
        "status": result.status,
        "total_frames": result.total_frames,
        "processed_frames": result.processed_frames,
        "result_video_path": result.result_video_path,
        "events": result.events,
        "detection_results": result.detection_results,
        "tracking_results": result.tracking_results,
        "error_message": result.error_message,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
