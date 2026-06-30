"""Export YOLOv11 model to ONNX format for faster inference.

ONNX models can run on CPU/GPU with lower latency and memory footprint.
Supports dynamic batch and fixed input size matching training imgsz.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ultralytics import YOLO


def export_onnx(
    model_path: str,
    output_path: str | None = None,
    imgsz: int = 960,
    opset: int = 17,
    simplify: bool = True,
    dynamic: bool = False,
    half: bool = False,
) -> Path:
    """Export YOLO model to ONNX format.

    Args:
        model_path: Path to .pt weights.
        output_path: Output .onnx path (default: same name as model).
        imgsz: Input image size matching training config.
        opset: ONNX opset version (12-20, default 17 for broad compatibility).
        simplify: Use onnxsim to simplify graph.
        dynamic: Export with dynamic batch dimension (batch=1 when False).
        half: FP16 export (reduces size 50%, requires GPU inference).

    Returns:
        Path to exported .onnx file.
    """
    source = Path(model_path)
    if not source.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    if output_path is None:
        output_path = source.with_suffix(".onnx")
    else:
        output_path = Path(output_path)

    print(f"Loading model: {source}")
    model = YOLO(str(source))

    print(f"Exporting to ONNX (imgsz={imgsz}, opset={opset}, simplify={simplify}, half={half}, dynamic={dynamic})")
    # YOLO.export leverages ultralytics native export pipeline
    exported = model.export(
        format="onnx",
        imgsz=imgsz,
        opset=opset,
        simplify=simplify,
        dynamic=dynamic,
        half=half,
    )

    # model.export returns the output path as string
    result_path = Path(str(exported))
    size_mb = result_path.stat().st_size / (1024 * 1024) if result_path.exists() else 0

    print(f"\nExport complete: {result_path} ({size_mb:.1f} MB)")

    if result_path != Path(output_path) and result_path.exists():
        import shutil
        shutil.move(str(result_path), str(output_path))
        print(f"Moved to: {output_path}")

    return Path(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export YOLOv11 to ONNX")
    parser.add_argument("--model", default="models/best.pt", help="Path to .pt weights")
    parser.add_argument("--output", default=None, help="Output .onnx path")
    parser.add_argument("--imgsz", type=int, default=960, help="Input image size")
    parser.add_argument("--opset", type=int, default=17, help="ONNX opset version")
    parser.add_argument("--no-simplify", action="store_true", help="Skip onnxsim simplification")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic batch size")
    parser.add_argument("--half", action="store_true", help="FP16 export")

    args = parser.parse_args()

    try:
        export_onnx(
            model_path=args.model,
            output_path=args.output,
            imgsz=args.imgsz,
            opset=args.opset,
            simplify=not args.no_simplify,
            dynamic=args.dynamic,
            half=args.half,
        )
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
