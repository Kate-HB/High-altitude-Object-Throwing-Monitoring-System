"""Minimal YOLO bbox annotation tool (OpenCV, works on Python 3.13).

Usage:
    python scripts/annotate.py data/falling_object/images/train data/falling_object/classes.txt

Controls:
    drag        - draw bbox (click top-left, drag to bottom-right, release)
    w/s         - prev/next image
    d           - delete selected bbox
    0-9         - select bbox
    space       - save current image labels
    q/esc       - quit

Output: labels/ dir with same-name .txt in YOLO format (class_id cx cy w h, normalized).
"""

import sys
import os
from pathlib import Path

import cv2
import numpy as np

# ── State ──────────────────────────────────────────────────────────────
STATE = {
    "image_idx": 0,
    "images": [],
    "labels_dir": None,
    "classes": [],
    "class_id": 0,
    "bboxes": [],        # list of (x1, y1, x2, y2, class_id) in pixel coords
    "drawing": False,
    "start_pt": None,    # (x, y)
    "current_pt": None,  # (x, y)
    "selected": -1,
    "img": None,         # current displayed image
    "orig_img": None,    # unmodified image
    "img_h": 0,
    "img_w": 0,
}

WINDOW = "Annotate"


# ── Helpers ─────────────────────────────────────────────────────────────
def load_labels(label_path, img_w, img_h):
    """Load existing YOLO labels from file, convert to pixel coords."""
    bboxes = []
    if label_path.exists():
        for line in label_path.read_text().strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 5:
                cls = int(float(parts[0]))
                cx = float(parts[1]) * img_w
                cy = float(parts[2]) * img_h
                w = float(parts[3]) * img_w
                h = float(parts[4]) * img_h
                x1 = int(cx - w / 2)
                y1 = int(cy - h / 2)
                x2 = int(cx + w / 2)
                y2 = int(cy + h / 2)
                bboxes.append([x1, y1, x2, y2, cls])
    return bboxes


def save_labels():
    """Save bboxes to YOLO format label file."""
    if STATE["label_path"] is None:
        return
    img_w, img_h = STATE["img_w"], STATE["img_h"]
    lines = []
    for x1, y1, x2, y2, cls in STATE["bboxes"]:
        x1c = max(0, x1)
        y1c = max(0, y1)
        x2c = min(img_w, x2)
        y2c = min(img_h, y2)
        w = x2c - x1c
        h = y2c - y1c
        if w <= 0 or h <= 0:
            continue
        cx = (x1c + x2c) / 2 / img_w
        cy = (y1c + y2c) / 2 / img_h
        nw = w / img_w
        nh = h / img_h
        lines.append(f"{cls} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
    STATE["label_path"].write_text("\n".join(lines) + ("\n" if lines else ""))


def draw_ui():
    """Redraw the canvas with all bboxes and UI hints."""
    img = STATE["orig_img"].copy()
    h, w = img.shape[:2]

    # Draw saved bboxes
    for i, (x1, y1, x2, y2, cls) in enumerate(STATE["bboxes"]):
        color = (0, 255, 0) if i != STATE["selected"] else (0, 255, 255)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{i}:{STATE['classes'][cls] if cls < len(STATE['classes']) else cls}"
        cv2.putText(img, label, (x1, max(y1 - 4, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # Draw in-progress bbox
    if STATE["drawing"] and STATE["start_pt"] and STATE["current_pt"]:
        cv2.rectangle(img, STATE["start_pt"], STATE["current_pt"], (255, 0, 0), 1)

    # Status bar
    total = len(STATE["images"])
    fn = os.path.basename(STATE["images"][STATE["image_idx"]]) if total else ""
    status = f" [{STATE['image_idx']+1}/{total}] {fn}  |  class: {STATE['class_id']} ({STATE['classes'][STATE['class_id']] if STATE['class_id'] < len(STATE['classes']) else STATE['class_id']})  |  bboxes: {len(STATE['bboxes'])}"
    bar = np.zeros((28, w, 3), dtype=np.uint8)
    bar[:] = (50, 50, 50)
    cv2.putText(bar, status, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    img = np.vstack([img, bar])

    STATE["img"] = img
    cv2.imshow(WINDOW, img)


def load_image():
    """Load current image and its existing labels."""
    path = STATE["images"][STATE["image_idx"]]
    img = cv2.imread(str(path))
    if img is None:
        print(f"WARN: cannot read {path}")
        return
    STATE["orig_img"] = img
    STATE["img_h"], STATE["img_w"] = img.shape[:2]
    STATE["selected"] = -1

    # Derive label path
    rel = Path(path).relative_to(STATE["base_image_dir"])
    label_name = Path(path).stem + ".txt"
    STATE["label_path"] = STATE["labels_dir"] / label_name

    STATE["bboxes"] = load_labels(STATE["label_path"], STATE["img_w"], STATE["img_h"])
    draw_ui()


def mouse_cb(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        STATE["drawing"] = True
        STATE["start_pt"] = (x, y)
        STATE["current_pt"] = (x, y)
        # Deselect
        STATE["selected"] = -1
        draw_ui()

    elif event == cv2.EVENT_MOUSEMOVE and STATE["drawing"]:
        STATE["current_pt"] = (x, y)
        draw_ui()

    elif event == cv2.EVENT_LBUTTONUP:
        STATE["drawing"] = False
        STATE["current_pt"] = (x, y)
        x1, y1 = STATE["start_pt"]
        x2, y2 = STATE["current_pt"]
        if abs(x2 - x1) > 3 and abs(y2 - y1) > 3:
            x1c, x2c = (min(x1, x2), max(x1, x2))
            y1c, y2c = (min(y1, y2), max(y1, y2))
            STATE["bboxes"].append([x1c, y1c, x2c, y2c, STATE["class_id"]])
            STATE["selected"] = len(STATE["bboxes"]) - 1
        STATE["start_pt"] = None
        STATE["current_pt"] = None
        draw_ui()


def handle_key(key):
    if key == ord("q") or key == 27:  # q or esc
        return False

    elif key == ord("w") or key == 82:  # w or up arrow
        save_labels()
        if STATE["image_idx"] > 0:
            STATE["image_idx"] -= 1
            load_image()

    elif key == ord("s") or key == 84:  # s or down arrow
        save_labels()
        if STATE["image_idx"] < len(STATE["images"]) - 1:
            STATE["image_idx"] += 1
            load_image()

    elif key == ord(" "):  # space — save
        save_labels()
        print(f"Saved: {STATE['label_path']}")

    elif key == ord("d"):  # delete selected
        if 0 <= STATE["selected"] < len(STATE["bboxes"]):
            del STATE["bboxes"][STATE["selected"]]
            STATE["selected"] = -1
            draw_ui()

    elif ord("0") <= key <= ord("9"):  # select bbox
        idx = key - ord("0")
        if idx < len(STATE["bboxes"]):
            STATE["selected"] = idx
            draw_ui()
        elif idx < len(STATE["classes"]):
            STATE["class_id"] = idx
            draw_ui()

    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    image_dir = Path(sys.argv[1])
    classes_file = Path(sys.argv[2])

    if not image_dir.is_dir():
        print(f"ERROR: {image_dir} is not a directory")
        sys.exit(1)
    if not classes_file.is_file():
        print(f"ERROR: {classes_file} not found")
        sys.exit(1)

    STATE["base_image_dir"] = image_dir
    STATE["classes"] = [line.strip() for line in classes_file.read_text().strip().splitlines() if line.strip()]
    if not STATE["classes"]:
        print("ERROR: classes.txt is empty")
        sys.exit(1)

    # Labels dir: sibling to images
    STATE["labels_dir"] = image_dir.parent / "labels" / image_dir.name
    os.makedirs(STATE["labels_dir"], exist_ok=True)

    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    STATE["images"] = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in exts])
    if not STATE["images"]:
        print(f"ERROR: no images found in {image_dir}")
        sys.exit(1)

    print(f"Images: {len(STATE['images'])}")
    print(f"Classes: {STATE['classes']}")
    print(f"Labels dir: {STATE['labels_dir']}")
    print("Controls: drag=draw bbox | w/s=prev/next | d=delete | 0-9=select/class | space=save | q=quit")

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, mouse_cb)
    load_image()

    while True:
        key = cv2.waitKey(0) & 0xFF
        if not handle_key(key):
            break

    save_labels()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
