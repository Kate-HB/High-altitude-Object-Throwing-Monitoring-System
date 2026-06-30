"""Run model inference on a video and save annotated output."""
import sys
from pathlib import Path
from ultralytics import YOLO

def main(model_path: str, video_path: str, conf: float = 0.25):
    model = YOLO(model_path)
    video_path = Path(video_path)
    out_dir = Path(r"C:\Users\27729\Desktop\High-altitude Object Throwing Monitoring System\outputs\test")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{video_path.stem}_pred.mp4"

    print(f"Model: {model_path}")
    print(f"Video: {video_path}")
    print(f"Output: {out_path}")
    print(f"Conf threshold: {conf}")
    print("Running inference...")

    results = model.predict(
        source=str(video_path),
        conf=conf,
        save=True,
        project=str(out_dir),
        name=video_path.stem,
        exist_ok=True,
        verbose=False,
        stream=True,
    )

    total_det = 0
    frames_with_det = 0
    total_frames = 0
    for r in results:
        n = len(r.boxes)
        total_det += n
        if n > 0:
            frames_with_det += 1
        total_frames += 1

    print(f"\nDone. Frames: {total_frames}, Detections: {total_det}, Positive frames: {frames_with_det}")
    if total_frames > 0:
        print(f"Detection rate: {100*frames_with_det/total_frames:.1f}% frames")


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\27729\Desktop\High-altitude Object Throwing Monitoring System\models\best.onnx"
    video = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\27729\Desktop\High-altitude Object Throwing Monitoring System\data\videos\demo.mp4"
    conf = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    main(model, video, conf)
