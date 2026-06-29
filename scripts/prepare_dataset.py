"""Prepare YOLO single-class dataset for falling object detection."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
CLASS_NAME = "falling_object"


def _iter_images(image_dir: Path) -> list[Path]:
    return sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def _normalize_label(source_label: Path, target_label: Path) -> bool:
    if not source_label.exists():
        target_label.write_text("", encoding="utf-8")
        return False

    lines = []
    for raw_line in source_label.read_text(encoding="utf-8").splitlines():
        parts = raw_line.strip().split()
        if len(parts) != 5:
            continue
        lines.append(" ".join(["0", *parts[1:]]))

    target_label.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")
    return True


def _write_dataset_files(output_dir: Path) -> None:
    (output_dir / "classes.txt").write_text(f"{CLASS_NAME}\n", encoding="utf-8")
    (output_dir / "data.yaml").write_text(
        "\n".join(
            [
                f"path: {output_dir.as_posix()}",
                "train: images/train",
                "val: images/val",
                "names:",
                f"  0: {CLASS_NAME}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prepare_dataset(source_dir: Path, output_dir: Path, val_ratio: float = 0.2) -> dict[str, int]:
    image_dir = source_dir / "images"
    label_dir = source_dir / "labels"
    if not image_dir.exists():
        raise FileNotFoundError(f"missing image directory: {image_dir}")

    images = _iter_images(image_dir)
    val_count = int(len(images) * val_ratio)
    if val_ratio > 0 and images and val_count == 0:
        val_count = 1
    train_count = len(images) - val_count

    summary = {"total_images": len(images), "train_images": train_count, "val_images": val_count, "missing_labels": 0}
    for split in ("train", "val"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    for index, image_path in enumerate(images):
        split = "train" if index < train_count else "val"
        target_image = output_dir / "images" / split / image_path.name
        target_label = output_dir / "labels" / split / f"{image_path.stem}.txt"
        shutil.copy2(image_path, target_image)
        has_label = _normalize_label(label_dir / f"{image_path.stem}.txt", target_label)
        if not has_label:
            summary["missing_labels"] += 1

    _write_dataset_files(output_dir)
    return summary


def extract_frames(video_dir: Path, frame_dir: Path, step: int = 10) -> int:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("cv2 is required for frame extraction") from exc

    frame_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for video_path in sorted(video_dir.glob("*")):
        cap = cv2.VideoCapture(str(video_path))
        frame_index = 0
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % step == 0:
                name = f"{video_path.stem}_{frame_index:06d}.jpg"
                cv2.imwrite(str(frame_dir / name), frame)
                written += 1
            frame_index += 1
        cap.release()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO falling_object dataset")
    parser.add_argument("--source", type=Path, required=True, help="source dir with images/ and labels/")
    parser.add_argument("--output", type=Path, required=True, help="output YOLO dataset dir")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--video-dir", type=Path, help="optional source videos for frame extraction")
    parser.add_argument("--frame-step", type=int, default=10)
    args = parser.parse_args()

    if args.video_dir:
        extract_frames(args.video_dir, args.source / "images", args.frame_step)
    summary = prepare_dataset(args.source, args.output, args.val_ratio)
    print(summary)


if __name__ == "__main__":
    main()
