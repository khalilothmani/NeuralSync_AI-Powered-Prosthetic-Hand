"""
main.py
=================
NeuralSync Prosthetic Hand — Main Control Loop

Entry point for the prosthetic hand controller.  Handles:
  - System startup / LED indication
  - Mode selection via physical switch (GPIO)
  - Mode 1: Normal EMG-triggered grab
  - Mode 2: AI-vision grab (YOLO object detection)

Run as root (or in the `gpio` group) on Raspberry Pi 5:
    sudo python3 main.py
    python3 main.py --simulate   # No hardware required

Mode 1 — Normal Mode
---------------------
  [Switch LEFT]
  EMG signal > threshold  → Grab 1 (POWER grab)
  EMG signal > threshold  → Grab 0 (RELEASE)
  (alternates between power grab and release on each trigger)

Mode 2 — AI Mode
-----------------
  [Switch RIGHT]
  EMG signal > threshold
    → flash torch, capture frame
    → run YOLO classification
    → if object recognised   → execute category grab + play sound
    → if object unrecognised → error buzz, wait for next trigger
  EMG signal > threshold (while gripping) → Grab 0 (RELEASE)
"""

import argparse
import logging
import signal
import sys
import time
import yaml
from pathlib import Path

# ── Logging setup (before any imports that use logger) ───────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("NeuralSync.main")

# ── Configuration ─────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

MODE_SWITCH_PIN = _CFG["gpio"]["mode_switch"]
POWER_LED_PIN   = _CFG["gpio"]["power_led"]

# ── Hardware simulation flag (set by --simulate CLI arg) ──────────────────────
_SIMULATE = False

# ── GPIO helpers ──────────────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False


def _gpio_setup():
    if not _GPIO_AVAILABLE:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MODE_SWITCH_PIN, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
    GPIO.setup(POWER_LED_PIN,   GPIO.OUT, initial=GPIO.LOW)


def _read_mode() -> int:
    """
    Return 1 (Normal) or 2 (AI) based on the physical switch position.
    HIGH = Mode 1 (pull-up; switch open); LOW = Mode 2 (switch closed to GND).
    """
    if not _GPIO_AVAILABLE:
        return 1   # Default to Mode 1 in simulation
    return 1 if GPIO.input(MODE_SWITCH_PIN) == GPIO.HIGH else 2


def _led_on():
    if _GPIO_AVAILABLE:
        GPIO.output(POWER_LED_PIN, GPIO.HIGH)


def _led_off():
    if _GPIO_AVAILABLE:
        GPIO.output(POWER_LED_PIN, GPIO.LOW)


# ── Main application ──────────────────────────────────────────────────────────

class NeuralSyncHand:
    """
    Orchestrates all subsystems of the prosthetic hand.

    State machine
    -------------
      IDLE         — hand is open, waiting for EMG trigger
      GRABBING     — hand is holding an object
    """

    def __init__(self):
        from src.servo_controller   import ServoController
        from src.emg_reader         import EMGReader
        from src.buzzer             import Buzzer
        from src.camera_handler     import CameraHandler
        from src.object_classifier  import ObjectClassifier

        logger.info("Initialising NeuralSync subsystems …")
        self.servos     = ServoController()
        self.emg        = EMGReader()
        self.buzzer     = Buzzer()
        self.camera     = CameraHandler()
        self.classifier = ObjectClassifier()

        self._state          = "IDLE"      # IDLE | GRABBING
        self._current_grab   = 0
        self._running        = True

        # Register SIGINT / SIGTERM handlers for clean shutdown
        signal.signal(signal.SIGINT,  self._on_shutdown)
        signal.signal(signal.SIGTERM, self._on_shutdown)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Boot sequence and main event loop."""
        _led_on()
        self.buzzer.play("system_on")

        mode = _read_mode()
        logger.info("NeuralSync started — Mode %d", mode)
        self.buzzer.play(f"mode_{mode}")

        logger.info("Entering main loop. Press Ctrl+C to exit.")
        self._main_loop()

    def _main_loop(self):
        prev_mode = None
        while self._running:
            mode = _read_mode()

            # Announce mode change
            if mode != prev_mode:
                logger.info("Mode changed → Mode %d (%s)",
                            mode, "Normal" if mode == 1 else "AI Vision")
                self.buzzer.play_async(f"mode_{mode}")
                prev_mode = mode
                # Always release the hand when changing modes
                if self._state == "GRABBING":
                    self._release()

            # ── EMG trigger check ──────────────────────────────────────────
            if self.emg.is_triggered():
                if self._state == "IDLE":
                    self._on_trigger_idle(mode)
                elif self._state == "GRABBING":
                    self._release()

            time.sleep(0.02)  # 50 Hz polling

    # ── Mode 1 — Normal ───────────────────────────────────────────────────────

    def _mode1_grab(self):
        """Activate the POWER grab (Grab 1) for Mode 1."""
        logger.info("[Mode 1] Activating POWER grab")
        self.servos.execute_grab(1)
        self.buzzer.play_async("grab_medium")
        self._state        = "GRABBING"
        self._current_grab = 1

    # ── Mode 2 — AI Vision ────────────────────────────────────────────────────

    def _mode2_grab(self):
        """
        Capture → classify → execute the appropriate grab.
        Returns False if classification failed (error, repeat).
        """
        logger.info("[Mode 2] EMG triggered — capturing image …")
        self.buzzer.play_async("capture")

        # Capture frame (torch fires inside CameraHandler.capture())
        try:
            img_path = self.camera.capture()
        except RuntimeError as exc:
            logger.error("Camera capture failed: %s", exc)
            self.buzzer.play("error")
            return False

        # Classify
        result = self.classifier.classify(img_path)

        if result.grab_id is None:
            logger.warning(
                "Object '%s' not in any category — signalling error.",
                result.detected_label or "none detected",
            )
            self.buzzer.play("error")
            return False

        # Execute grab
        grab_name = self.servos.execute_grab(result.grab_id)
        logger.info(
            "[Mode 2] Object='%s' category=%s → %s (Grab %d)",
            result.detected_label, result.category, grab_name, result.grab_id,
        )
        self.buzzer.play_async(result.sound_key)
        self._state        = "GRABBING"
        self._current_grab = result.grab_id
        return True

    # ── Shared trigger handler ────────────────────────────────────────────────

    def _on_trigger_idle(self, mode: int):
        if mode == 1:
            self._mode1_grab()
        else:
            self._mode2_grab()  # Retries not needed — next EMG trigger will retry

    def _release(self):
        logger.info("Releasing hand → Grab 0 (OPEN)")
        self.servos.execute_grab(0)
        self.buzzer.play_async("release")
        self._state        = "IDLE"
        self._current_grab = 0

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def _on_shutdown(self, signum, frame):
        logger.info("Shutdown signal received — cleaning up …")
        self._running = False
        self._release()
        self.servos.shutdown()
        self.camera.release()
        self.buzzer.close()
        _led_off()
        if _GPIO_AVAILABLE:
            GPIO.cleanup()
        logger.info("NeuralSync shut down cleanly. Goodbye.")
        sys.exit(0)


# ── CLI entry point ───────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="NeuralSync Prosthetic Hand Controller"
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Run without hardware (simulation mode)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    _SIMULATE = args.simulate

    _gpio_setup()
    hand = NeuralSyncHand()
    hand.start()
