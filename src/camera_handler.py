"""
camera_handler.py
====================
Manages the Raspberry Pi Camera 2 (5 MP) for the NeuralSync hand.

Workflow (AI mode)
------------------
  1. Flash the digital torch (GPIO) for consistent illumination.
  2. Warm up the camera (discard initial auto-exposure frames).
  3. Capture a single high-quality frame.
  4. Save the frame to a temp file (returned for YOLO analysis).
  5. Switch off the torch.

The camera is accessed via OpenCV's VideoCapture with the
V4L2 backend (libcamera-apps must expose /dev/video0).

Wiring (torch)
--------------
  GPIO 22 → NPN transistor base (via 1 kΩ resistor)
  Transistor collector → Torch LED (+)
  Torch LED (-) → GND
  Transistor emitter → GND
"""

import cv2
import time
import logging
import yaml
from pathlib import Path

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("RPi.GPIO not found — camera handler in simulation mode.")

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

CAM_IDX        = _CFG["camera"]["device_index"]
CAP_W          = _CFG["camera"]["capture_width"]
CAP_H          = _CFG["camera"]["capture_height"]
WARMUP_FRAMES  = _CFG["camera"]["warmup_frames"]
TORCH_PIN      = _CFG["gpio"]["torch"]

# Saved frame path (temp, in project root)
_FRAME_PATH = Path(__file__).resolve().parent.parent / "captured_frame.jpg"


class CameraHandler:
    """
    Provides a ``capture()`` method that returns the path to a JPEG
    image of the scene directly in front of the prosthetic hand.

    The torch is automatically flashed during capture to ensure
    adequate lighting in poor ambient conditions.

    Usage
    -----
        cam = CameraHandler()
        img_path = cam.capture()   # returns Path to JPEG
        cam.release()
    """

    def __init__(self):
        # GPIO torch setup
        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(TORCH_PIN, GPIO.OUT, initial=GPIO.LOW)
            logger.info("Torch configured on GPIO %d (BCM).", TORCH_PIN)

        # Open camera
        self._cap = cv2.VideoCapture(CAM_IDX, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAP_W)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_H)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # Always get latest frame

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera at index {CAM_IDX}. "
                "Check that libcamera-compat or v4l2 is enabled."
            )
        logger.info(
            "Camera %d opened at %dx%d.", CAM_IDX, CAP_W, CAP_H
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def capture(self, save_path: Path = None) -> Path:
        """
        Flash the torch, capture one frame, save it as JPEG.

        Parameters
        ----------
        save_path : Path | None
            Where to save the captured image.  Defaults to
            ``<project_root>/captured_frame.jpg``.

        Returns
        -------
        Path
            Absolute path to the saved JPEG file.
        """
        if save_path is None:
            save_path = _FRAME_PATH

        self._torch_on()
        try:
            # Warm-up: flush stale buffered frames
            for _ in range(WARMUP_FRAMES):
                self._cap.grab()

            success, frame = self._cap.read()
            if not success or frame is None:
                raise RuntimeError("Camera capture failed — no frame received.")

            cv2.imwrite(str(save_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
            logger.info("Frame captured and saved to %s", save_path)
        finally:
            self._torch_off()

        return save_path.resolve()

    def release(self):
        """Release camera and clean up GPIO."""
        self._torch_off()
        if self._cap.isOpened():
            self._cap.release()
        if RPI_AVAILABLE:
            GPIO.cleanup(TORCH_PIN)
        logger.info("CameraHandler released.")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _torch_on(self):
        logger.debug("Torch ON")
        if RPI_AVAILABLE:
            GPIO.output(TORCH_PIN, GPIO.HIGH)
        time.sleep(0.12)     # Allow LEDs to stabilise before capture

    def _torch_off(self):
        logger.debug("Torch OFF")
        if RPI_AVAILABLE:
            GPIO.output(TORCH_PIN, GPIO.LOW)


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    cam = CameraHandler()
    try:
        path = cam.capture()
        print(f"Saved: {path}")
    finally:
        cam.release()
