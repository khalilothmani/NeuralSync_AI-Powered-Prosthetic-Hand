"""
object_classifier.py
=========================
YOLO-based object classification for the NeuralSync AI mode.

The classifier receives a captured image path, runs YOLOv11x
inference, identifies the most-confident detected object, and
maps it to one of 5 grab categories.

Grab Category → Grab ID mapping
---------------------------------
  SENSITIVE  → Grab 2   (soft partial grip for fragile objects)
  LIGHT      → Grab 3   (light cylindrical grip)
  MEDIUM     → Grab 1   (power grasp — same as Mode 1 default)
  HEAVY      → Grab 1   (power grasp with full finger closure)
  PINCH      → Grab 4   (two-finger: thumb + index)
  UNKNOWN    → None     (error — trigger error buzzer, repeat capture)

Object lists are intentionally large to handle everyday objects
encountered in domestic and clinical environments.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

YOLO_MODEL  = Path(__file__).resolve().parent.parent / _CFG["yolo"]["model_path"]
YOLO_CONF   = _CFG["yolo"]["confidence"]
YOLO_IOU    = _CFG["yolo"]["iou_threshold"]
YOLO_DEVICE = _CFG["yolo"]["device"]

# ── Object Category Lists ─────────────────────────────────────────────────────
#
# Each list contains YOLO class label strings (lowercase, as returned by
# the COCO dataset used to pre-train YOLOv11x).
# Custom fine-tuned labels can be added here freely.

SENSITIVE_OBJECTS: list[str] = [
    # Fragile / crushable — needs softest grip (Grab 2)
    "egg", "eggshell", "light_bulb", "lightbulb", "glass", "wine_glass",
    "wine glass", "champagne_glass", "christmas_ornament", "ornament",
    "snowglobe", "snow globe", "soap_bubble", "bubble", "balloon",
    "paper_cup", "styrofoam_cup", "styrofoam cup", "thin_glass",
    "crystal_glass", "crystal glass", "porcelain_cup", "cracker",
    "biscuit", "chip", "potato_chip", "tortilla_chip", "wafer",
    "strawberry", "cherry", "blueberry", "raspberry", "grape",
    "flower", "rose", "tulip", "daisy", "petal", "soap",
    "soap_bar", "ice_cream_cone", "cone", "cupcake", "macaron",
    "meringue", "marshmallow", "cotton_ball", "cotton_pad",
    "pill", "tablet", "capsule", "contact_lens_case", "lens_case",
    "test_tube", "petri_dish", "microchip", "sim_card", "sd_card",
    "watch", "wristwatch", "pocket_watch", "reading_glasses",
    "eyeglasses", "spectacles", "sunglasses", "monocle",
    "ornamental_egg", "plastic_bag", "sandwich_bag",
    "vase", "ceramic_bowl", "porcelain_plate", "fine_china",
]

LIGHT_OBJECTS: list[str] = [
    # Lightweight — gentle cylindrical grip (Grab 3)
    "cup", "mug", "coffee_mug", "tea_cup", "paper_cup", "plastic_cup",
    "fork", "spoon", "teaspoon", "chopsticks", "straw",
    "pen", "pencil", "marker", "highlighter", "crayon", "chalk",
    "eraser", "ruler", "bookmark", "paper", "sheet_of_paper",
    "notebook", "notepad", "sticky_note", "post_it", "index_card",
    "envelope", "letter", "card", "greeting_card", "postcard",
    "tissue", "napkin", "paper_towel", "toilet_paper",
    "plastic_bottle_empty", "empty_bottle",
    "orange", "apple", "pear", "peach", "plum", "kiwi", "mango",
    "lemon", "lime", "tangerine", "nectarine", "apricot",
    "small_tomato", "cherry_tomato", "avocado",
    "bread_roll", "dinner_roll", "croissant", "muffin", "bagel",
    "donut", "doughnut", "cookie", "brownie",
    "remote_control", "tv_remote", "game_controller",
    "mouse", "computer_mouse", "small_toy",
    "hairbrush", "comb", "toothbrush", "razor",
    "lipstick", "mascara", "eyeliner", "makeup_brush",
    "candle", "small_candle",
    "sponge", "scrubber",
    "headphones", "earbuds", "earphone",
    "small_book", "paperback",
    "banana", "carrot", "celery_stalk", "cucumber_small",
    "glove", "sock", "handkerchief",
    "USB_drive", "usb drive", "flash_drive", "memory_stick",
    "key", "keys", "keychain", "lanyard",
]

MEDIUM_OBJECTS: list[str] = [
    # Medium weight — power grasp (Grab 1)
    "bottle", "plastic_bottle", "water_bottle_small",
    "can", "soda_can", "beer_can", "tin_can",
    "book", "hardcover", "textbook", "binder", "folder",
    "wallet", "purse", "clutch", "small_handbag",
    "apple_large", "tomato", "bell_pepper", "potato", "onion",
    "corn", "cob", "zucchini", "broccoli", "cauliflower",
    "eggplant", "butternut_squash", "grapefruit",
    "sandwich", "burger", "hot_dog", "hotdog", "taco",
    "burrito", "wrap", "sub",
    "plate", "bowl", "dish",
    "hammer", "screwdriver", "wrench", "pliers",
    "knife", "kitchen_knife", "bread_knife",
    "scissors", "shears",
    "smartphone", "mobile_phone", "cell_phone", "phone",
    "camera", "digital_camera", "compact_camera",
    "tablet", "ipad",
    "jar", "mason_jar", "jam_jar", "peanut_butter_jar",
    "thermos", "flask", "travel_mug",
    "shoe", "sneaker", "boot",
    "helmet", "hat", "cap",
    "toy", "action_figure", "lego",
    "stapler", "tape_dispenser", "hole_punch",
    "deodorant", "cologne_bottle", "perfume_bottle",
    "shampoo_bottle", "conditioner_bottle",
    "drill_bit", "chisel", "file_tool",
    "flashlight", "torch",
    "binoculars", "magnifying_glass",
    "mouse_pad", "keyboard",
    "clock", "alarm_clock",
]

HEAVY_OBJECTS: list[str] = [
    # Heavy — full power grasp (Grab 1, max torque)
    "water_bottle", "water bottle", "1kg_bottle", "large_bottle",
    "bottle_of_water", "gallon_jug", "milk_jug", "juice_jug",
    "wine_bottle", "beer_bottle", "whiskey_bottle", "spirit_bottle",
    "paint_can", "bucket",
    "pot", "cooking_pot", "saucepan", "skillet", "frying_pan",
    "cast_iron", "dutch_oven",
    "brick", "rock", "stone",
    "dumbbell", "weight_plate", "kettlebell",
    "toolbox", "power_drill", "electric_drill",
    "laptop", "notebook_computer",
    "book_heavy", "encyclopedia",
    "dictionary",
    "large_jar", "pickle_jar",
    "fire_extinguisher",
    "car_battery",
    "pumpkin", "watermelon", "melon", "cabbage", "head_of_lettuce",
    "iron", "clothes_iron",
    "blender_jar", "food_processor",
    "power_bank", "large_power_bank",
    "hardcover_book_set",
    "can_of_paint",
    "bag_of_sugar", "bag_of_flour",
    "suitcase_handle", "briefcase",
]

PINCH_OBJECTS: list[str] = [
    # Small / thin — two-finger pinch (thumb + index, Grab 4)
    "coin", "penny", "nickel", "dime", "quarter",
    "screw", "bolt", "nut", "washer", "nail",
    "button", "sewing_button", "pin", "safety_pin",
    "needle", "sewing_needle",
    "chip", "microchip", "resistor", "capacitor", "transistor",
    "USB_connector", "usb connector", "cable_end", "plug",
    "ring", "earring", "stud_earring", "bead", "pearl",
    "gem", "gemstone", "jewel",
    "stamp", "postage_stamp",
    "playing_card", "card", "business_card",
    "credit_card", "id_card", "loyalty_card",
    "sim_card", "micro_sim", "nano_sim",
    "memory_card", "microsd", "sd_card",
    "battery_aa", "battery_aaa", "battery_9v", "battery",
    "clip", "paper_clip", "binder_clip", "hairclip", "hairpin",
    "toothpick", "match", "matchstick",
    "sugar_packet", "salt_packet",
    "band_aid", "plaster", "adhesive_bandage",
    "thumb_drive", "nano_usb",
    "key_fob", "car_key",
    "dice", "die", "small_pebble",
]

# ── Grab mapping ──────────────────────────────────────────────────────────────

CATEGORY_TO_GRAB: dict[str, int] = {
    "SENSITIVE": 2,
    "LIGHT":     3,
    "MEDIUM":    1,
    "HEAVY":     1,
    "PINCH":     4,
}

CATEGORY_SOUND: dict[str, str] = {
    "SENSITIVE": "grab_sensitive",
    "LIGHT":     "grab_light",
    "MEDIUM":    "grab_medium",
    "HEAVY":     "grab_heavy",
    "PINCH":     "grab_pinch",
}


@dataclass
class ClassificationResult:
    """Result returned by :meth:`ObjectClassifier.classify`."""
    detected_label: str          # YOLO class name
    confidence: float            # Detection confidence (0–1)
    category: Optional[str]      # 'SENSITIVE' | 'LIGHT' | 'MEDIUM' | 'HEAVY' | 'PINCH' | None
    grab_id: Optional[int]       # 0–4, or None if unknown
    sound_key: Optional[str]     # Buzzer pattern key


class ObjectClassifier:
    """
    Wraps a YOLOv11x model to detect and categorise objects.

    Parameters
    ----------
    model_path : str | Path | None
        Override the model path from config.yaml.
    """

    # Category lookup table (label → category)
    _LOOKUP: dict[str, str] = (
        {lbl: "SENSITIVE" for lbl in SENSITIVE_OBJECTS}
        | {lbl: "LIGHT"     for lbl in LIGHT_OBJECTS}
        | {lbl: "MEDIUM"    for lbl in MEDIUM_OBJECTS}
        | {lbl: "HEAVY"     for lbl in HEAVY_OBJECTS}
        | {lbl: "PINCH"     for lbl in PINCH_OBJECTS}
    )

    def __init__(self, model_path=None):
        from ultralytics import YOLO
        path = Path(model_path) if model_path else YOLO_MODEL
        logger.info("Loading YOLO model from %s …", path)
        self._model = YOLO(str(path))
        logger.info("YOLO model loaded.")

    def classify(self, image_path: Path | str) -> ClassificationResult:
        """
        Run YOLO inference on the image and return a ClassificationResult.

        The method picks the single detection with the highest confidence
        and looks it up in the category lists.

        Parameters
        ----------
        image_path : Path | str
            Path to a JPEG/PNG image file.

        Returns
        -------
        ClassificationResult
        """
        image_path = str(image_path)
        logger.info("Running YOLO inference on: %s", image_path)

        results = self._model.predict(
            source=image_path,
            conf=YOLO_CONF,
            iou=YOLO_IOU,
            device=YOLO_DEVICE,
            verbose=False,
        )

        if not results or len(results[0].boxes) == 0:
            logger.warning("No objects detected in the frame.")
            return ClassificationResult(
                detected_label="",
                confidence=0.0,
                category=None,
                grab_id=None,
                sound_key=None,
            )

        # Pick the highest-confidence detection
        boxes  = results[0].boxes
        best_i = int(boxes.conf.argmax())
        conf   = float(boxes.conf[best_i])
        cls_id = int(boxes.cls[best_i])
        label  = results[0].names[cls_id].lower().replace(" ", "_")

        category = self._lookup_category(label)
        grab_id  = CATEGORY_TO_GRAB.get(category)
        sound    = CATEGORY_SOUND.get(category)

        logger.info(
            "Detected '%s' (conf=%.2f) → category=%s  grab=%s",
            label, conf, category, grab_id,
        )

        return ClassificationResult(
            detected_label=label,
            confidence=conf,
            category=category,
            grab_id=grab_id,
            sound_key=sound,
        )

    def _lookup_category(self, label: str) -> Optional[str]:
        """
        Look up a YOLO label in the category lists.
        Tries exact match first, then partial substring match.
        """
        # Normalise
        label_clean = label.lower().replace("-", "_").replace(" ", "_")

        # Exact match
        if label_clean in self._LOOKUP:
            return self._LOOKUP[label_clean]

        # Partial match — check if the label contains or is contained in any key
        for key, cat in self._LOOKUP.items():
            if key in label_clean or label_clean in key:
                return cat

        return None


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    img = sys.argv[1] if len(sys.argv) > 1 else "captured_frame.jpg"
    clf = ObjectClassifier()
    res = clf.classify(img)
    print(f"\nLabel    : {res.detected_label}")
    print(f"Conf     : {res.confidence:.2f}")
    print(f"Category : {res.category}")
    print(f"Grab ID  : {res.grab_id}")
    print(f"Sound    : {res.sound_key}")
