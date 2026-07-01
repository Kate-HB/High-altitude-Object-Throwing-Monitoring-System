"""YOLOv11 training script for falling_object detection.

Configurable epochs, batch, imgsz, lr — run from CLI or import as module.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ultralytics import YOLO


def train(
    data_yaml: str | Path,
    model_weights: str = "yolo11n.pt",
    epochs: int = 60,
    batch: int = 8,
    imgsz: int = 960,
    device: str = "0",
    workers: int = 4,
    cache: bool = True,
    optimizer: str = "AdamW",
    lr0: float = 0.001,
    lrf: float = 0.01,
    cos_lr: bool = True,
    patience: int = 20,
    close_mosaic: int = 10,
    freeze: int = 5,
    mosaic: float = 1.0,
    box: float = 10.0,
    cls: float = 0.8,
    scale: float = 0.3,
    copy_paste: float = 0.3,
    project: str = "runs/train",
    name: str = "falling_object",
) -> Path:
    """Run YOLOv11 training and return path to best.pt.

    All parameters map directly to ultralytics training args.
    Sensible defaults for 4GB GPUs (RTX 3050 Laptop).
    """
    model = YOLO(model_weights)
    model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        workers=workers,
        cache=cache,
        optimizer=optimizer,
        lr0=lr0,
        lrf=lrf,
        cos_lr=cos_lr,
        patience=patience,
        close_mosaic=close_mosaic,
        freeze=freeze,
        mosaic=mosaic,
        box=box,
        cls=cls,
        scale=scale,
        copy_paste=copy_paste,
        project=project,
        name=name,
    )
    best = Path(project) / name / "weights" / "best.pt"
    if best.exists():
        print(f"\nTraining done. Best weights: {best}")
    else:
        print(f"\nTraining finished but best.pt not found at {best}", file=sys.stderr)
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description="Train YOLOv11 for falling_object detection")
    parser.add_argument("--data", type=str, default="data/falling_object/data.yaml", help="YOLO data.yaml path")
    parser.add_argument("--weights", type=str, default="yolo11n.pt", help="pretrained weights path")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cache", action="store_true", default=True)
    parser.add_argument("--optimizer", type=str, default="AdamW")
    parser.add_argument("--lr0", type=float, default=0.001)
    parser.add_argument("--lrf", type=float, default=0.01)
    parser.add_argument("--cos-lr", action="store_true", default=True)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--close-mosaic", type=int, default=10)
    parser.add_argument("--freeze", type=int, default=5)
    parser.add_argument("--mosaic", type=float, default=1.0)
    parser.add_argument("--box", type=float, default=10.0)
    parser.add_argument("--cls", type=float, default=0.8, dest="cls_loss")
    parser.add_argument("--scale", type=float, default=0.3)
    parser.add_argument("--copy-paste", type=float, default=0.3)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="falling_object")

    args = parser.parse_args()

    # Windows OpenMP workaround
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "1")

    train(
        data_yaml=args.data,
        model_weights=args.weights,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=args.workers,
        cache=args.cache,
        optimizer=args.optimizer,
        lr0=args.lr0,
        lrf=args.lrf,
        cos_lr=args.cos_lr,
        patience=args.patience,
        close_mosaic=args.close_mosaic,
        freeze=args.freeze,
        mosaic=args.mosaic,
        box=args.box,
        cls=args.cls_loss,
        scale=args.scale,
        copy_paste=args.copy_paste,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()
