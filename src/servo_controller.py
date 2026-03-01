"""
servo_controller.py
=====================
Controls the 6 servo motors of the NeuralSync prosthetic hand
via the PCA9685 PWM driver over I2C.

Hardware layout
---------------
  Channel 0  — Index finger  (flex)
  Channel 1  — Middle finger (flex)
  Channel 2  — Ring finger   (flex)
  Channel 3  — Pinky finger  (flex)
  Channel 4  — Thumb rotation (opposition axis)
  Channel 5  — Thumb flex

Grab catalogue
--------------
  Grab 0 — RELEASE   : Default open hand (all fingers extended)
  Grab 1 — POWER     : Full power grasp (cylindrical / medium-hard)
  Grab 2 — SENSITIVE : Soft, partial closure for fragile objects
  Grab 3 — LIGHT     : Light-force cylindrical grip
  Grab 4 — PINCH     : Two-finger (thumb + index only)

Each grab is executed as a smooth, interpolated movement to
avoid jerking, which could damage fragile objects or shed
attached EMG leads.
"""

import time
import logging
import yaml
from pathlib import Path

try:
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo as adafruit_servo
    import board
    import busio
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("Adafruit PCA9685 libraries not found — running in simulation mode.")

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

PCA_ADDR      = _CFG["pca9685"]["i2c_address"]
PCA_FREQ      = _CFG["pca9685"]["frequency"]
SRV           = _CFG["servos"]
LIM           = _CFG["servo_limits"]

# Servo channel indices
IDX_INDEX    = SRV["index_finger"]
IDX_MIDDLE   = SRV["middle_finger"]
IDX_RING     = SRV["ring_finger"]
IDX_PINKY    = SRV["pinky_finger"]
IDX_THUMB_R  = SRV["thumb_rotation"]
IDX_THUMB_F  = SRV["thumb_flex"]

# Tick shortcuts
OPEN        = LIM["open_tick"]
MID_OPEN    = LIM["mid_open_tick"]
NEUTRAL     = LIM["neutral_tick"]
MID_CLOSE   = LIM["mid_close_tick"]
CLOSED      = LIM["closed_tick"]

# ── Grab definitions (ticks per channel) ─────────────────────────────────────
# Format: [index, middle, ring, pinky, thumb_rot, thumb_flex]

GRAB_PROFILES = {
    #                 IDX       MID       RING      PINKY     THB_R     THB_F
    0: {  # RELEASE — full open, thumb relaxed
        "name": "RELEASE",
        "ticks": [OPEN, OPEN, OPEN, OPEN, OPEN, OPEN],
        "speed": 0.008,   # seconds per tick increment (fast release)
    },
    1: {  # POWER — cylindrical power grasp (medium-hard)
        "name": "POWER",
        "ticks": [CLOSED, CLOSED, CLOSED, CLOSED, MID_CLOSE, MID_CLOSE],
        "speed": 0.006,
    },
    2: {  # SENSITIVE — soft partial closure for fragile objects
        "name": "SENSITIVE",
        "ticks": [MID_OPEN, MID_OPEN, MID_OPEN, MID_OPEN, NEUTRAL, MID_OPEN],
        "speed": 0.012,   # slower = more gentle
    },
    3: {  # LIGHT — lighter cylindrical grip for light objects
        "name": "LIGHT",
        "ticks": [MID_CLOSE, MID_CLOSE, MID_CLOSE, NEUTRAL, NEUTRAL, NEUTRAL],
        "speed": 0.008,
    },
    4: {  # PINCH — two-finger (thumb + index only)
        "name": "PINCH",
        "ticks": [MID_CLOSE, OPEN, OPEN, OPEN, CLOSED, MID_CLOSE],
        "speed": 0.010,
    },
}


class ServoController:
    """
    High-level interface to the 6 servo motors of the NeuralSync hand.

    Usage
    -----
        ctrl = ServoController()
        ctrl.execute_grab(1)   # Power grasp
        ctrl.execute_grab(0)   # Release / open hand
    """

    def __init__(self):
        self._current_ticks = [OPEN] * 6       # Track live positions
        self._current_grab  = 0

        if RPI_AVAILABLE:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._pca = PCA9685(i2c, address=PCA_ADDR)
            self._pca.frequency = PCA_FREQ
            logger.info("PCA9685 initialised at address 0x%02X, freq=%dHz", PCA_ADDR, PCA_FREQ)
        else:
            self._pca = None
            logger.info("Simulation mode — no hardware connected.")

        # Ensure the hand starts fully open
        self._set_all_ticks([OPEN] * 6)

    # ── Public API ───────────────────────────────────────────────────────────

    def execute_grab(self, grab_id: int) -> str:
        """
        Smoothly transition to the target grab posture.

        Parameters
        ----------
        grab_id : int
            0 = RELEASE | 1 = POWER | 2 = SENSITIVE | 3 = LIGHT | 4 = PINCH

        Returns
        -------
        str
            Name of the grab executed (e.g. "POWER").
        """
        if grab_id not in GRAB_PROFILES:
            raise ValueError(f"Invalid grab_id '{grab_id}'. Valid: 0-4.")

        profile     = GRAB_PROFILES[grab_id]
        target      = profile["ticks"]
        speed       = profile["speed"]
        name        = profile["name"]

        logger.info("Executing grab %d (%s)", grab_id, name)
        self._smooth_move(target, speed)
        self._current_grab = grab_id
        return name

    def release(self):
        """Open the hand to the default resting position."""
        self.execute_grab(0)

    def get_current_grab(self) -> int:
        """Return the ID of the currently active grab."""
        return self._current_grab

    def shutdown(self):
        """Release the hand and de-energise all servos."""
        self.release()
        if self._pca:
            time.sleep(0.5)
            self._pca.deinit()
        logger.info("ServoController shut down.")

    # ── Private helpers ──────────────────────────────────────────────────────

    def _smooth_move(self, target_ticks: list[int], speed: float):
        """
        Linearly interpolate each servo from its current position to the
        target tick value.  All servos move simultaneously.

        Parameters
        ----------
        target_ticks : list[int]
            Desired PCA tick value for each of the 6 channels.
        speed : float
            Seconds to wait between each 1-tick increment.
            Smaller = faster.  Typical range: 0.005–0.015.
        """
        start  = list(self._current_ticks)
        deltas = [t - s for s, t in zip(start, target_ticks)]
        steps  = max(abs(d) for d in deltas) or 1

        for step in range(1, steps + 1):
            intermediate = [
                round(start[i] + deltas[i] * step / steps)
                for i in range(6)
            ]
            self._set_all_ticks(intermediate)
            time.sleep(speed)

        self._current_ticks = list(target_ticks)

    def _set_all_ticks(self, ticks: list[int]):
        """Write raw PWM ticks to all 6 servo channels at once."""
        for channel, tick in enumerate(ticks):
            self._set_channel(channel, tick)

    def _set_channel(self, channel: int, tick: int):
        """
        Write a PWM tick to a single PCA9685 channel.
        Clamps the value to the hardware-safe range [OPEN, CLOSED].
        """
        tick = max(OPEN, min(CLOSED, tick))
        if self._pca:
            # PCA9685 channel: off_time tick at start=0
            self._pca.channels[channel].duty_cycle = int(tick / 4096 * 65535)
        else:
            logger.debug("SIM ch%d → %d ticks", channel, tick)


# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    ctrl = ServoController()
    try:
        for gid in [1, 4, 2, 3, 0]:
            name = ctrl.execute_grab(gid)
            print(f"Grab {gid} ({name}) executed — sleeping 2s")
            time.sleep(2)
    finally:
        ctrl.shutdown()
