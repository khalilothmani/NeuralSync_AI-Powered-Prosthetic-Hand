# ⚙️ NeuralSync — Software Setup Guide

## Prerequisites

- **Hardware**: Raspberry Pi 5 (minimum 4 GB RAM recommended)
- **OS**: Raspberry Pi OS Bookworm (64-bit) — latest version
- **Python**: 3.11+ (included with Bookworm)
- **Internet connection** for initial package installation

---

## 1. Raspberry Pi OS Initial Setup

### Flash the SD card
```bash
# Use rpi-imager on your PC to write Raspberry Pi OS (64-bit) Bookworm
# Enable SSH, set hostname, Wi-Fi during the imager process
```

### Update the system
```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

---

## 2. Enable Required Interfaces

```bash
sudo raspi-config
```

Navigate to **Interface Options** and enable:

| Interface | Purpose |
|-----------|---------|
| **I2C** | ADS1115 + PCA9685 communication |
| **Camera** | Raspberry Pi Camera 2 |
| **SSH** | Remote development (optional) |

Then reboot:
```bash
sudo reboot
```

### Add your user to the I²C and GPIO groups
```bash
sudo usermod -aG i2c,gpio,video $USER
```
Log out and back in for group changes to take effect.

---

## 3. Camera Setup (Raspberry Pi Camera 2)

Verify the camera module is detected:
```bash
rpicam-hello
```

If using V4L2 / OpenCV (used by NeuralSync):
```bash
sudo apt install -y libcamera-dev libcamera-ipa python3-libcamera
# Enable V4L2 compat driver:
echo 'bcm2835-v4l2' | sudo tee -a /etc/modules
sudo modprobe bcm2835-v4l2
```

Test:
```bash
v4l2-ctl --list-devices
# Should show: /dev/video0
```

---

## 4. System-level Python Packages

```bash
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libopencv-dev python3-opencv        # OpenCV from apt (faster)
sudo apt install -y python3-rpi.gpio                    # RPi.GPIO
sudo apt install -y i2c-tools                           # i2cdetect utility
```

---

## 5. Clone the Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/NeuralSync.git
cd NeuralSync
```

---

## 6. Python Virtual Environment

```bash
python3 -m venv venv --system-site-packages
# --system-site-packages lets the venv access system OpenCV and RPi.GPIO
source venv/bin/activate
```

---

## 7. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note**: The first run of `pip install ultralytics` will download ~600MB of
> PyTorch dependencies. Ensure you have internet access and disk space.

---

## 8. Download the YOLO Model

```bash
# From within the NeuralSync directory:
python3 -c "from ultralytics import YOLO; YOLO('yolo11x.pt')"
```

This downloads `yolo11x.pt` (~109 MB) and saves it in the current directory.

> Alternatively, copy your existing `yolo11x.pt` to the project root.

---

## 9. Verify I²C Devices

```bash
sudo i2cdetect -y 1
```

Expected output (devices connected):
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --   ← PCA9685
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --   ← ADS1115
```

---

## 10. Configuration

All configurable parameters are in **`config/config.yaml`**:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `emg.threshold` | `10000` | Raw ADC value to trigger a grab |
| `emg.cooldown_seconds` | `1.0` | Minimum seconds between triggers |
| `emg.channel` | `0` | ADS1115 channel (AIN0) |
| `gpio.mode_switch` | `17` | BCM GPIO for mode toggle switch |
| `gpio.power_led` | `27` | BCM GPIO for green power LED |
| `gpio.torch` | `22` | BCM GPIO for torch/flashlight |
| `gpio.buzzer` | `18` | BCM GPIO for passive buzzer |
| `yolo.confidence` | `0.35` | YOLO minimum detection confidence |
| `camera.warmup_frames` | `5` | Frames discarded before capture |

### Calibrating the EMG Threshold

1. Run the logger:
   ```bash
   python3 -c "
   from src.emg_reader import EMGReader
   import time
   r = EMGReader()
   for _ in range(200):
       print(r.read_raw())
       time.sleep(0.05)
   "
   ```
2. Observe readings at rest (baseline) and during contraction (peak).
3. Set `emg.threshold` to ~80% of your peak contraction value in `config.yaml`.

---

## 11. Running NeuralSync

### Normal operation (hardware required)
```bash
source venv/bin/activate
sudo python3 main.py
```

> `sudo` is required for GPIO access. To avoid sudo, add your user to the `gpio`
> group (step 4) and use udev rules for I²C/PWM — advanced, see RPi forums.

### Simulation mode (no hardware)
```bash
python3 main.py --simulate
```

### Debug logging
```bash
sudo python3 main.py --log-level DEBUG
```

---

## 12. Auto-start on Boot (systemd)

Create a systemd service to start NeuralSync automatically:

```bash
sudo nano /etc/systemd/system/neuralsync.service
```

Paste:
```ini
[Unit]
Description=NeuralSync Prosthetic Hand Controller
After=multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/YOUR_USERNAME/NeuralSync
Environment=PYTHONPATH=/home/YOUR_USERNAME/NeuralSync
ExecStart=/home/YOUR_USERNAME/NeuralSync/venv/bin/python3 main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable neuralsync
sudo systemctl start neuralsync
sudo systemctl status neuralsync
```

---

## 13. Troubleshooting

| Problem | Solution |
|---------|---------|
| `FileNotFoundError: yolo11x.pt` | Download model: `python3 -c "from ultralytics import YOLO; YOLO('yolo11x.pt')"` |
| `OSError: [Errno 121] Remote I/O error` | Check I²C wiring, verify with `i2cdetect -y 1` |
| Camera not found `/dev/video0` | Run `sudo modprobe bcm2835-v4l2`, check ribbon cable |
| EMG never triggers | Lower `emg.threshold` in `config.yaml`, check ADS1115 AIN0 wiring |
| Servos jitter or don't move | Check 5V servo power supply, verify PCA9685 address is `0x40` |
| `ModuleNotFoundError: RPi.GPIO` | Install: `sudo apt install python3-rpi.gpio` |
