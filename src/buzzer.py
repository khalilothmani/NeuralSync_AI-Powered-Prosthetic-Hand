"""
buzzer.py
================
Generates buzzer feedback patterns using a passive buzzer driven
via GPIO PWM on the Raspberry Pi 5.

Wiring
------
  Buzzer (+) → GPIO 18  (PWM0 / BCM 18)
  Buzzer (-) → GND

The buzzer is a passive piezo element — it requires a PWM square
wave to produce sound.  RPi.GPIO software PWM is used; for lower
jitter, consider using hardware PWM (pigpio).
"""

import time
import logging
import threading
import yaml
from pathlib import Path

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("RPi.GPIO not found — buzzer running in simulation mode.")

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

BUZZER_PIN      = _CFG["gpio"]["buzzer"]
PATTERNS        = _CFG["buzzer_patterns"]


class Buzzer:
    """
    Controls a passive piezo buzzer via GPIO PWM.

    Usage
    -----
        bz = Buzzer()
        bz.play("system_on")         # play by pattern name
        bz.beep(frequency=440, duration_ms=200)   # single beep
        bz.play_async("grab_medium") # non-blocking
        bz.close()
    """

    def __init__(self):
        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUZZER_PIN, GPIO.OUT)
            self._pwm = GPIO.PWM(BUZZER_PIN, 440)
            logger.info("Buzzer initialised on GPIO %d (BCM).", BUZZER_PIN)
        else:
            self._pwm = None
            logger.info("Buzzer: simulation mode.")

    # ── Public API ────────────────────────────────────────────────────────────

    def beep(self, frequency: int = 440, duration_ms: int = 200):
        """
        Emit a single tone.

        Parameters
        ----------
        frequency : int
            Tone in Hz.
        duration_ms : int
            Duration in milliseconds.
        """
        logger.debug("BEEP  freq=%d Hz  dur=%d ms", frequency, duration_ms)
        if self._pwm:
            self._pwm.ChangeFrequency(frequency)
            self._pwm.start(50)            # 50% duty cycle
            time.sleep(duration_ms / 1000)
            self._pwm.stop()
        else:
            print(f"[SIM] BEEP {frequency}Hz {duration_ms}ms")

    def play(self, pattern_name: str):
        """
        Play a named pattern from config.yaml buzzer_patterns.

        Parameters
        ----------
        pattern_name : str
            Key from the ``buzzer_patterns`` section in config.yaml.
        """
        pattern = PATTERNS.get(pattern_name)
        if pattern is None:
            logger.warning("Unknown buzzer pattern: '%s'", pattern_name)
            return
        for freq, dur_ms in pattern:
            self.beep(frequency=freq, duration_ms=dur_ms)
            time.sleep(0.05)               # brief gap between notes

    def play_async(self, pattern_name: str):
        """Play a pattern in a background thread (non-blocking)."""
        t = threading.Thread(target=self.play, args=(pattern_name,), daemon=True)
        t.start()

    def error_buzz(self):
        """Three harsh low beeps — object not recognised."""
        self.play("error")

    def close(self):
        """Clean up GPIO resources."""
        if self._pwm:
            self._pwm.stop()
        if RPI_AVAILABLE:
            GPIO.cleanup(BUZZER_PIN)
        logger.info("Buzzer closed.")


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    bz = Buzzer()
    print("Testing all patterns...")
    for name in PATTERNS:
        print(f"  → {name}")
        bz.play(name)
        time.sleep(0.3)
    bz.close()
