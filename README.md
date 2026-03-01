# 🦾 NeuralSync — AI-Powered Prosthetic Hand

<div align="center">

![NeuralSync Banner](https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/robot_header_banner.jpeg)

**NeuralSync** is an open-source, AI-enhanced prosthetic hand powered by a Raspberry Pi 5.  
It reads muscle signals via an EMG sensor, classifies objects with YOLOv11x computer vision,  
and drives 6 servo motors to perform 5 distinct grip patterns autonomously.

<br>

<p align="center">
  <img src="https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/robot_full_view.jpeg" width="600" alt="NeuralSync Full View">
  <br>
  <i>Full view of the NeuralSync robotic hand.</i>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Ultralytics YOLOv11](https://img.shields.io/badge/YOLO-v11x-orange.svg)](https://ultralytics.com)
[![Raspberry Pi 5](https://img.shields.io/badge/RPi-5-red.svg)](https://raspberrypi.com)

</div>

---

## 📖 Table of Contents

- [Overview](#overview)
- [Hardware Components](#hardware-components)
- [System Architecture](#system-architecture)
- [Operating Modes](#operating-modes)
- [Grip Profiles](#grip-profiles)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Wiring](#wiring)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

NeuralSync replaces a missing hand with an intelligent robotic limb. It operates in two modes:

| Mode | Activation | Description |
|------|-----------|-------------|
| **Mode 1 — Normal** | Switch LEFT | EMG threshold → Power Grab / Release toggle |
| **Mode 2 — AI Vision** | Switch RIGHT | EMG threshold → Camera flash → YOLO classify → Adaptive Grab |

The hand uses a **passive return system** (elastic bands) to reopen fingers,  
with servos providing the closing force only — reducing heat and power draw.

<p align="center">
  <video src="https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/robot_360_rotation.mp4" width="600" autoplay loop muted playsinline></video>
  <br>
  <i>360° Viewing angles of the robotic assembly.</i>
</p>

---

## Hardware Components

| Component | Model / Spec | Role |
|-----------|-------------|------|
| Microcomputer | Raspberry Pi 5 | Main controller |
| EMG Sensor | Generic surface EMG module | Muscle signal acquisition |
| ADC | ADS1115 (16-bit, I²C) | Analog → Digital conversion |
| Servo Driver | PCA9685 (16-ch PWM, I²C) | Servo motor control |
| Servo Motors × 6 | MG90S / SG90 (5V) | 4 fingers + 2 thumb axes |
| Camera | Raspberry Pi Camera Module 2 (5 MP) | Object detection |
| Torch / Flash | Digital LED torch (GPIO controlled) | Illuminate capture scene |
| Buzzer | Passive piezo buzzer | Audio feedback |
| Mode Switch | SPDT toggle switch | Mode 1 ↔ Mode 2 |
| Power LED | Green 5mm LED | System ON indicator |
| EMG Power | 4 × 3.7 V LiPo (2S2P) | Dedicated EMG sensor supply |
| RPi Power | 2 × 3.7 V LiPo (2S1P) | Raspberry Pi 5V supply |

### EMG Sensor Power Wiring
The EMG module requires a **bipolar supply** from the 4-cell LiPo pack:

```
Battery arrangement (4 × 3.7V):
  [Cell A+] ──┐
              ├── Series → (+) terminal ≈ +7.4V → EMG V+
  [Cell A-] ──┤
              ├── Mid-point → GND / Reference
  [Cell B+] ──┤
              ├── Series → (−) terminal ≈ −7.4V → EMG V−
  [Cell B-] ──┘
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi 5                            │
│                                                                  │
│   ┌─────────────┐    I²C     ┌──────────────┐                   │
│   │  ADS1115    │◄──────────►│   main.py    │                   │
│   │  (EMG ADC)  │           │              │                   │
│   └─────────────┘           │  Mode 1:     │                   │
│                             │  EMG → Grab  │                   │
│   ┌─────────────┐    I²C     │              │                   │
│   │  PCA9685    │◄──────────►│  Mode 2:     │                   │
│   │ Servo Driver│           │  EMG →       │                   │
│   └──────┬──────┘           │  Camera →    │                   │
│          │ PWM×6            │  YOLO →      │                   │
│   ┌──────▼──────────────┐   │  Grab        │                   │
│   │ 6 × Servo Motors    │   └──────────────┘                   │
│   │ (Index/Middle/Ring/ │        │  GPIO                        │
│   │  Pinky/Thumb×2)     │        ├── Torch (GPIO22)            │
│   └─────────────────────┘        ├── Buzzer (GPIO18)           │
│                                  ├── Power LED (GPIO27)         │
│   ┌─────────────────────┐        └── Mode Switch (GPIO17)       │
│   │ RPi Camera 2 (5MP)  │                                        │
│   │ → captured_frame.jpg│◄── libcamera / V4L2                   │
│   └─────────────────────┘                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Operating Modes

### Mode 1 — Normal Mode 💪

The hand mimics a simple toggle mechanism:

1. **IDLE state** → EMG spike above threshold → **POWER GRAB** (Grab 1) activates
2. **GRABBING state** → next EMG spike → **RELEASE** (Grab 0)

Use for everyday grasping tasks where AI classification is not needed.

<p align="center">
  <img src="https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/robot_hand_open.jpeg" width="400" alt="Hand Open State">
  <br>
  <i>Robot hand in its default open state.</i>
</p>

### Mode 2 — AI Vision Mode 🤖

Full object-aware adaptive gripping:

1. EMG spike → torch flashes → camera captures one frame  
2. YOLOv11x analyses the frame and identifies the object  
3. Object is matched to one of 5 categories (see [Grip Profiles](#grip-profiles))  
4. Appropriate grip executes + buzzer confirms  
5. Object **not recognised** → error buzzer → hand stays open → repeat  
6. Second EMG spike (while gripping) → RELEASE

> See [`docs/MODES.md`](docs/MODES.md) for full detail.

---

## Grip Profiles

| Grab ID | Name | Fingers Used | Use Case |
|---------|------|-------------|----------|
| 0 | **RELEASE** | All open | Default / reset state |
| 1 | **POWER** | All fingers + thumb full close | Bottle, tool, cylindrical objects |
| 2 | **SENSITIVE** | Partial close, slow motion | Egg, glass, fragile items |
| 3 | **LIGHT** | 3/4 close, moderate force | Pen, fruit, paper cup |
| 4 | **PINCH** | Thumb + Index only | Coin, key, chip, small objects |

<p align="center">
  <video src="https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/robot_grabbing_demo.mp4" width="400" autoplay loop muted playsinline></video>
  <br>
  <i>Demonstration of the power grab functionality.</i>
</p>

> See [`docs/GRABS.md`](docs/GRABS.md) for servo angles and mechanical details.

---

## Repository Structure

```
NeuralSync/
├── main.py                    # Entry point — main control loop
├── hand_vision.py                 # Diagnostic YOLO viewer (desktop/testing)
├── yolo11x.pt                 # YOLOv11x weights (download separately)
├── requirements.txt           # Python dependencies
├── .gitignore
├── LICENSE
│
├── config/
│   └── config.yaml            # All hardware pins, thresholds, servo limits
│
├── src/
│   ├── __init__.py
│   ├── servo_controller.py    # PCA9685 servo control + 5 grab classes
│   ├── emg_reader.py          # ADS1115 EMG signal reader + threshold detect
│   ├── camera_handler.py      # Camera capture with torch flash
│   ├── buzzer.py              # Passive buzzer feedback patterns
│   └── object_classifier.py  # YOLOv11x inference + 5-category mapping
│
├── docs/
│   ├── WIRING.md              # Full circuit / wiring guide + ASCII diagrams
│   ├── SETUP.md               # Software installation & configuration
│   ├── GRABS.md               # Grip profiles, servo angles, mechanics
│   ├── MODES.md               # Mode 1 & 2 detailed flowcharts
│   └── OBJECT_LISTS.md        # Full grab-category object lists
│
└── assets/
    ├── robot_header_banner.jpeg   # README banner image
    ├── robot_hand_open.jpeg       # Hand in open state
    ├── robot_grabbing_demo.mp4    # Power grab demonstration
    ├── robot_full_view.jpeg       # Full assembly view
    ├── circuit_overview.jpeg      # Hardware wiring overview
    └── robot_360_rotation.mp4     # 360 rotation showcase
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/NeuralSync.git
cd NeuralSync
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Download the YOLO model

```bash
python3 -c "from ultralytics import YOLO; YOLO('yolo11x.pt')"
# This auto-downloads yolo11x.pt (~109 MB) to the current directory
```

> If you already have `yolo11x.pt`, place it in the project root.

### 4. Enable I²C on Raspberry Pi

```bash
sudo raspi-config
# → Interface Options → I2C → Enable
```

### 5. Enable Camera

```bash
sudo raspi-config
# → Interface Options → Camera → Enable
# For Camera 2 add to /boot/config.txt:
# camera_auto_detect=1
```

### 6. Run the hand controller

```bash
sudo python3 main.py
# or with verbose logging:
sudo python3 main.py --log-level DEBUG
# Simulation (no hardware):
python3 main.py --simulate
```

### 7. Run the YOLO diagnostic viewer (optional, needs display)

```bash
python3 hand_vision.py                         # Webcam
python3 hand_vision.py --source image.jpg      # Static image
python3 hand_vision.py --labels                # Print all 80 COCO classes + categories
python3 hand_vision.py --categories egg water_bottle coin  # Query grab category
```

---

## Wiring

See **[`docs/WIRING.md`](docs/WIRING.md)** for the complete pin-by-pin connection guide including:

- I²C Bus (ADS1115 + PCA9685)
- GPIO pins (switch, LED, torch, buzzer)
- EMG sensor bipolar power supply
- RPi 5 power from 2S1P LiPo
- PCA9685 → Servo cable routing

<p align="center">
  <img src="https://raw.githubusercontent.com/khalilothmani/NeuralSync_AI-Powered-Prosthetic-Hand/master/assets/circuit_overview.jpeg" width="600" alt="Circuit Overview">
  <br>
  <i>General overview of the electronic circuit.</i>
</p>

---

## Documentation

| Document | Contents |
|---------|---------|
| [`docs/SETUP.md`](docs/SETUP.md) | Raspberry Pi OS setup, Python venv, I²C/camera config |
| [`docs/WIRING.md`](docs/WIRING.md) | Full hardware wiring / circuit guide |
| [`docs/GRABS.md`](docs/GRABS.md) | Grip profile mechanics and servo tick tables |
| [`docs/MODES.md`](docs/MODES.md) | Mode 1 & 2 state machine diagrams |
| [`docs/OBJECT_LISTS.md`](docs/OBJECT_LISTS.md) | All YOLO grab-category object lists |

---

## Contributing

Pull requests are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Commit your changes: `git commit -m "Add: feature description"`
4. Push: `git push origin feature/my-improvement`
5. Open a Pull Request

---

## License

MIT License — see [`LICENSE`](LICENSE) for details.

---

<div align="center">
Built with ❤️ and 🤖 — NeuralSync Project
</div>
