"""
emg_reader.py
===================
Reads the raw analog EMG signal from the muscle sensor module
via the ADS1115 16-bit ADC over I2C.

Wiring
------
  EMG module OUT → ADS1115 AIN0
  ADS1115 VCC    → 3.3 V (RPi)
  ADS1115 GND    → GND
  ADS1115 SDA    → GPIO 2  (SDA1)
  ADS1115 SCL    → GPIO 3  (SCL1)
  ADS1115 ADDR   → GND  → I2C address 0x48

EMG sensor power: 4 × 3.7 V LiPo arranged as 2S2P
  (+) = positive output rail → EMG module V+
  (-) = negative output rail → EMG module GND / reference

The EMG module outputs a 0–3.3 V analog signal proportional to
muscle activation intensity.  The ADS1115 converts this to a
16-bit signed integer (0–32767 for 0–3.3 V at ±4.096 V gain).
"""

import time
import logging
import yaml
from pathlib import Path

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("ADS1115 libraries not found — running in simulation mode.")

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
with open(_CONFIG_PATH) as f:
    _CFG = yaml.safe_load(f)

EMG_ADDR      = _CFG["emg"]["i2c_address"]
EMG_CHANNEL   = _CFG["emg"]["channel"]
THRESHOLD     = _CFG["emg"]["threshold"]
COOLDOWN      = _CFG["emg"]["cooldown_seconds"]


class EMGReader:
    """
    Continuously monitors EMG signal and fires a callback when
    muscle activation exceeds the configured threshold.

    Parameters
    ----------
    threshold : int | None
        Override the config-file threshold for this instance.
    on_trigger : callable | None
        Function called with no arguments each time the threshold
        is exceeded (after the cooldown window has elapsed).
    """

    def __init__(self, threshold: int = None, on_trigger=None):
        self.threshold   = threshold if threshold is not None else THRESHOLD
        self.on_trigger  = on_trigger
        self._last_trig  = 0.0           # epoch seconds of last trigger
        self._running    = False

        if RPI_AVAILABLE:
            i2c        = busio.I2C(board.SCL, board.SDA)
            self._ads  = ADS.ADS1115(i2c, address=EMG_ADDR)
            self._chan = AnalogIn(self._ads, getattr(ADS, f"P{EMG_CHANNEL}"))
            self._ads.gain = 1           # ±4.096 V range → full 16-bit resolution
            logger.info(
                "ADS1115 initialised at 0x%02X, channel=%d, threshold=%d",
                EMG_ADDR, EMG_CHANNEL, self.threshold,
            )
        else:
            self._ads  = None
            self._chan = None
            logger.info("EMGReader: simulation mode.")

    # ── Public API ────────────────────────────────────────────────────────────

    def read_raw(self) -> int:
        """
        Return the instantaneous raw ADC reading (0–32767).
        In simulation mode returns 0.
        """
        if self._chan:
            return self._chan.value
        return 0

    def read_voltage(self) -> float:
        """Return the channel voltage in volts."""
        if self._chan:
            return self._chan.voltage
        return 0.0

    def is_triggered(self) -> bool:
        """
        Returns True if EMG exceeds the threshold AND the cooldown
        period has elapsed since the last valid trigger.
        Calling this method DOES update the trigger timestamp.
        """
        now = time.monotonic()
        if now - self._last_trig < COOLDOWN:
            return False
        value = self.read_raw()
        logger.debug("EMG raw=%d (threshold=%d)", value, self.threshold)
        if value >= self.threshold:
            self._last_trig = now
            logger.info("EMG TRIGGERED  raw=%d", value)
            return True
        return False

    def poll_blocking(self, poll_interval: float = 0.02):
        """
        Blocking poll loop — calls ``on_trigger`` every time the
        threshold is exceeded.  Run in a separate thread if needed.
        
        Stops when ``stop()`` is called.
        """
        self._running = True
        logger.info("EMGReader: polling started (interval=%.3fs)", poll_interval)
        while self._running:
            if self.is_triggered():
                if self.on_trigger:
                    self.on_trigger()
            time.sleep(poll_interval)
        logger.info("EMGReader: polling stopped.")

    def stop(self):
        """Signal the polling loop to exit."""
        self._running = False


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    def _on_trig():
        print(">>> TRIGGER!")

    reader = EMGReader(on_trigger=_on_trig)
    print("Monitoring EMG — press Ctrl+C to stop.")
    try:
        reader.poll_blocking(poll_interval=0.02)
    except KeyboardInterrupt:
        reader.stop()
        print("Done.")
