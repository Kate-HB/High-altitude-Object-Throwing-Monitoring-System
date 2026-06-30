"""Evaluate YOLOv11 model: Precision, Recall, mAP50, mAP50-95.

Runs on validation set specified in data.yaml. Outputs per-class and
aggregate metrics in a format suitable for 7/3 defense presentation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ultralytics import YOLO


def evaluate(
    model_path: str,
    data_yaml: str,
    imgsz: int = 960,
    device: str = "0",
    conf: float = 0.001,
    iou: float = 0.7,
    save_json: bool = True,
    save_plots: bool = True,
) -> dict[str, Any]:
    """Run validation and return metrics dict.

    Args:
        model_path: Path to trained .pt weights.
        data_yaml: Path to dataset config (YOLO format).
        imgsz: Image size matching training.
        device: CUDA device string or "cpu".
        conf: Confidence threshold for validation.
        iou: IoU threshold for validation.
        save_json: Write results to JSON file.
        save_plots: Generate confusion matrix, PR curve, etc.

    Returns:
        Dict with keys: precision, recall, mAP50, mAP50-95, fps, model_info.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    model = YOLO(str(model_path))

    print(f"Evaluating {model_path.name} on {data_yaml}")
    print(f"  imgsz={imgsz}, conf={conf}, iou={iou}, device={device}")

    metrics = model.val(
        data=data_yaml,
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        device=device,
        split="val",
        plots=save_plots,
        save_json=save_json,
    )

    # Extract key metrics from ultralytics Results object
    result: dict[str, Any] = {
        "model": str(model_path),
        "dataset": str(data_yaml),
        "imgsz": imgsz,
        "metrics": {
            "precision": round(float(metrics.box.mp), 4),
            "recall": round(float(metrics.box.mr), 4),
            "mAP50": round(float(metrics.box.map50), 4),
            "mAP50_95": round(float(metrics.box.map), 4),
        },
        "speed": {
            "preprocess_ms": round(float(metrics.speed.get("preprocess", 0)), 2),
            "inference_ms": round(float(metrics.speed.get("inference", 0)), 2),
            "postprocess_ms": round(float(metrics.speed.get("postprocess", 0)), 2),
        },
    }

    # Try to get FPS from speed
    if result["speed"]["inference_ms"] > 0:
        result["speed"]["fps"] = round(1000.0 / result["speed"]["inference_ms"], 1)

    print(f"\n{'='*50}")
    print(f"Precision:  {result['metrics']['precision']}")
    print(f"Recall:     {result['metrics']['recall']}")
    print(f"mAP@50:     {result['metrics']['mAP50']}")
    print(f"mAP@50-95:  {result['metrics']['mAP50_95']}")
    print(f"Inference:  {result['speed']['inference_ms']} ms/frame")
    if "fps" in result["speed"]:
        print(f"FPS:        {result['speed']['fps']}")

    # Save results
    out_dir = Path("outputs/eval")
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / f"{model_path.stem}_metrics.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nResults saved to: {result_path}")

    if save_plots:
        # Plots are saved by ultralytics to runs/detect/val*
        print("Plots saved in runs/detect/val*/")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate YOLOv11 model metrics")
    parser.add_argument("--model", default="models/best.pt", help="Path to .pt weights")
    parser.add_argument("--data", default="data/falling_object/data.yaml", help="Dataset YAML")
    parser.add_argument("--imgsz", type=int, default=960, help="Image size")
    parser.add_argument("--device", default="0", help="CUDA device")
    parser.add_argument("--conf", type=float, default=0.001, help="Val confidence threshold")
    parser.add_argument("--iou", type=float, default=0.7, help="Val IoU threshold")
    parser.add_argument("--no-plots", action="store_true", help="Skip plot generation")

    args = parser.parse_args()

    try:
        evaluate(
            model_path=args.model,
            data_yaml=args.data,
            imgsz=args.imgsz,
            device=args.device,
            conf=args.conf,
            iou=args.iou,
            save_plots=not args.no_plots,
        )
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
