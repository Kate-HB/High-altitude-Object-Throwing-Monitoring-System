"""Extract frames from a video."""
import sys
from pathlib import Path
import cv2

def main(video_path: str, prefix: str = "frame", step: int = 1):
    video = Path(video_path)
    out_dir = video.parent / f"{video.stem}_frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video: {fps:.1f}fps, {total} frames, step={step}")

    saved = 0
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            cv2.imwrite(str(out_dir / f"{prefix}_{saved:06d}.jpg"), frame)
            saved += 1
        idx += 1
        if idx % 1000 == 0:
            print(f"  {idx}/{total}")

    cap.release()
    print(f"Done: {saved} frames -> {out_dir}")

if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else None
    prefix = sys.argv[2] if len(sys.argv) > 2 else "frame"
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    if video:
        main(video, prefix, step)
    else:
        print("Usage: python extract_frames.py <video_path> [prefix] [step]")
