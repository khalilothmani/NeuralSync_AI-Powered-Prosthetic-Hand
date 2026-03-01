"""
hand_vision.py
==============
NeuralSync — Live object detection viewer (for desktop testing).

Run this on a PC or the Raspberry Pi with a display attached to
visually verify that the YOLOv11x model correctly detects and
classifies objects that the hand will encounter.

This is NOT the runtime classifier (see src/object_classifier.py).
This script is a diagnostic / demonstration tool.

Usage
-----
    python3 hand_vision.py                    # Use default webcam
    python3 hand_vision.py --source 1         # Use /dev/video1
    python3 hand_vision.py --source image.jpg # Run on a static image
    python3 hand_vision.py --labels           # Print all known class labels
    python3 hand_vision.py --categories egg water_bottle coin  # Lookup categories
"""

import argparse
import sys
import cv2
from pathlib import Path
from ultralytics import YOLO

# Load classifier lists for colour-coding detections by grab category
sys.path.insert(0, str(Path(__file__).parent))
from src.object_classifier import (
    SENSITIVE_OBJECTS, LIGHT_OBJECTS, MEDIUM_OBJECTS,
    HEAVY_OBJECTS, PINCH_OBJECTS, CATEGORY_TO_GRAB,
)

# ── Colour map (BGR) for each grab category ───────────────────────────────────
CATEGORY_COLORS = {
    "SENSITIVE": (0,   200, 255),   # Amber
    "LIGHT":     (0,   255, 120),   # Green
    "MEDIUM":    (255, 180,   0),   # Blue
    "HEAVY":     (0,    80, 255),   # Red-orange
    "PINCH":     (255,   0, 200),   # Magenta
    "UNKNOWN":   (128, 128, 128),   # Grey
}

MODEL_PATH  = Path(__file__).parent / "yolo11x.pt"


def _lookup_category(label: str) -> str:
    label = label.lower().replace(" ", "_").replace("-", "_")
    if label in {l.lower().replace(" ", "_") for l in SENSITIVE_OBJECTS}: return "SENSITIVE"
    if label in {l.lower().replace(" ", "_") for l in LIGHT_OBJECTS}:     return "LIGHT"
    if label in {l.lower().replace(" ", "_") for l in MEDIUM_OBJECTS}:    return "MEDIUM"
    if label in {l.lower().replace(" ", "_") for l in HEAVY_OBJECTS}:     return "HEAVY"
    if label in {l.lower().replace(" ", "_") for l in PINCH_OBJECTS}:     return "PINCH"
    return "UNKNOWN"


def run_live(source):
    """Stream YOLO detections with category-coloured bounding boxes."""
    model = YOLO(str(MODEL_PATH))
    cap   = cv2.VideoCapture(source, cv2.CAP_V4L2 if isinstance(source, int) else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"NeuralSync Hand Vision — source={source}  |  q to quit")

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        results = model.predict(frame, conf=0.30, iou=0.45, verbose=False)

        for box in results[0].boxes:
            cls_id   = int(box.cls[0])
            conf     = float(box.conf[0])
            label    = results[0].names[cls_id]
            category = _lookup_category(label)
            color    = CATEGORY_COLORS[category]
            grab_id  = CATEGORY_TO_GRAB.get(category, "?")

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            text = f"{label} [{category}/G{grab_id}] {conf:.0%}"
            cv2.putText(frame, text, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        cv2.imshow("NeuralSync — YOLOv11x Category Viewer", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def run_image(path: str):
    """Run detection on a single image and display results."""
    model  = YOLO(str(MODEL_PATH))
    frame  = cv2.imread(path)
    if frame is None:
        print(f"Error: cannot open image '{path}'")
        sys.exit(1)

    results = model.predict(frame, conf=0.30, iou=0.45, verbose=False)
    for box in results[0].boxes:
        cls_id   = int(box.cls[0])
        conf     = float(box.conf[0])
        label    = results[0].names[cls_id]
        category = _lookup_category(label)
        color    = CATEGORY_COLORS[category]
        grab_id  = CATEGORY_TO_GRAB.get(category, "?")

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{label} [{category}/G{grab_id}] {conf:.0%}"
        cv2.putText(frame, text, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        print(f"  {label:30s}  conf={conf:.2f}  category={category}  grab={grab_id}")

    cv2.imshow("NeuralSync — Static Image Detection", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def print_labels():
    model  = YOLO(str(MODEL_PATH))
    names  = model.names
    print(f"\nYOLO model has {len(names)} classes:\n")
    for k, v in sorted(names.items()):
        cat   = _lookup_category(v)
        grab  = CATEGORY_TO_GRAB.get(cat, "-")
        print(f"  {k:4d}  {v:35s}  [{cat}/G{grab}]")


def lookup_categories(labels: list[str]):
    for lbl in labels:
        cat  = _lookup_category(lbl)
        grab = CATEGORY_TO_GRAB.get(cat, "-")
        print(f"  {lbl:30s} → {cat:10s}  Grab {grab}")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeuralSync Hand Vision — YOLOv11x Object Viewer")
    parser.add_argument("--source",     default="0",
                        help="Camera index (int) or image/video path")
    parser.add_argument("--labels",     action="store_true",
                        help="Print all YOLO class labels with categories")
    parser.add_argument("--categories", nargs="+", metavar="LABEL",
                        help="Look up grab category for label(s)")
    args = parser.parse_args()

    if args.labels:
        print_labels()
    elif args.categories:
        lookup_categories(args.categories)
    else:
        try:
            source = int(args.source)
        except ValueError:
            source = args.source

        if isinstance(source, str) and Path(source).is_file():
            run_image(source)
        else:
            run_live(source)
