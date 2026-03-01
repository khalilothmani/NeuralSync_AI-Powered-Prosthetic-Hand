# 🔌 NeuralSync — Wiring & Circuit Guide

This document covers every hardware connection in the NeuralSync prosthetic hand.

---

## 1. I²C Bus Overview

Both the **ADS1115** (EMG ADC) and **PCA9685** (servo driver) share the Raspberry Pi 5's  
hardware I²C bus (Bus 1).

```
Raspberry Pi 5 GPIO Header
──────────────────────────
  Pin 1   [3.3V] ──┬──────────────────────── ADS1115 VDD
                   └──────────────────────── PCA9685 VCC
  Pin 3   [SDA1] ──┬──────────────────────── ADS1115 SDA
    (GPIO 2)       └──────────────────────── PCA9685 SDA
  Pin 5   [SCL1] ──┬──────────────────────── ADS1115 SCL
    (GPIO 3)       └──────────────────────── PCA9685 SCL
  Pin 6   [GND]  ──┬──────────────────────── ADS1115 GND
                   └──────────────────────── PCA9685 GND

Pull-up resistors: 4.7 kΩ from SDA → 3.3V and SCL → 3.3V
(Usually built into the ADS1115 & PCA9685 breakout boards)
```

### I²C Addresses

| Device | Address | ADDR pin |
|--------|---------|---------|
| ADS1115 | `0x48` | ADDR → GND |
| PCA9685 | `0x40` | Default (A0-A5 = GND) |

Verify with:
```bash
sudo i2cdetect -y 1
```

---

## 2. ADS1115 (EMG ADC) Wiring

```
ADS1115 Breakout
────────────────
  VDD  ──── 3.3V  (RPi Pin 1)
  GND  ──── GND   (RPi Pin 6)
  SDA  ──── SDA1  (RPi Pin 3 / GPIO2)
  SCL  ──── SCL1  (RPi Pin 5 / GPIO3)
  ADDR ──── GND   → address 0x48
  AIN0 ──── EMG sensor OUT (signal wire)
  AIN1 ──── NC (not connected)
  AIN2 ──── NC
  AIN3 ──── NC
```

> **Important**: AIN0 is the EMG signal input. The ADS1115 measures
> AIN0 relative to GND (single-ended mode, GAIN=1, ±4.096V range).

---

## 3. EMG Sensor Power Supply

The EMG module requires a **bipolar supply**. Use 4 × 3.7V LiPo cells:

```
Cell Layout (4 cells physially in 2 pairs):

  [+] Cell 1A ─── (+) Cell 1B ─── V+ terminal (~+7.4V) → EMG V+
                              ║
                          GND rail ─────────────────────── EMG GND/REF
                              ║
  [-] Cell 2A ─── (-) Cell 2B ─── V− terminal (~−7.4V) → EMG V−

Wiring summary:
  EMG V+  ← Series pair positive terminal  (+7.4V)
  EMG GND ← Mid-point between the two pairs  (0V reference)
  EMG V−  ← Series pair negative terminal  (−7.4V)

EMG OUT signal wire ────────────────────────────────→ ADS1115 AIN0
EMG GND ────────────────────────────────────────────→ ADS1115 GND (shared)
```

> ⚠️ Do NOT connect the EMG bipolar supply GND to the RPi 3.3V rail.
> Only share the **signal GND** at the ADS1115 input side.

---

## 4. PCA9685 → Servo Motors

The PCA9685 provides **50Hz PWM** signals to all 6 servos.  
Servos are powered from a **separate 5V 3A** supply (not from RPi 5V pin!).

```
PCA9685 Breakout
─────────────────
  VCC  ──── 3.3V (RPi Pin 1)  ← Logic supply only
  GND  ──── GND  (RPi Pin 6)
  SDA  ──── SDA1 (RPi Pin 3)
  SCL  ──── SCL1 (RPi Pin 5)
  OE   ──── NC   (active low; leave floating = enabled)

  V+   ──── 5V servo power supply POSITIVE
  GND  ──── 5V servo power supply NEGATIVE

Servo channel assignments:
  Channel 0 ── Index finger flex servo    (Signal / Red / Brown wires)
  Channel 1 ── Middle finger flex servo
  Channel 2 ── Ring finger flex servo
  Channel 3 ── Pinky finger flex servo
  Channel 4 ── Thumb rotation servo       (opposition axis)
  Channel 5 ── Thumb flex servo

Each servo connector (3-pin JST or Dupont):
  PWM signal ← PCA9685 channel signal pin (yellow/white)
  +5V        ← PCA9685 V+ rail (red)
  GND        ← PCA9685 GND rail (brown/black)
```

---

## 5. GPIO Peripheral Connections

All BCM pin numbers. Use 3.3V logic.

### 5.1 Mode Switch (SPDT Toggle)

```
SPDT Switch:
  Common   ──── GPIO 17 (BCM) — RPi Pin 11
  Position1──── 3.3V (RPi Pin 1)   → Mode 1 (HIGH)
  Position2──── GND  (RPi Pin 6)   → Mode 2 (LOW)

Internal pull-up is enabled in software (GPIO.PUD_UP).
HIGH = Mode 1 (Normal), LOW = Mode 2 (AI Vision).
```

### 5.2 Power LED (Green)

```
  GPIO 27 (BCM) — RPi Pin 13
    │
   330Ω resistor
    │
   LED (+) anode
   LED (−) cathode ──── GND (RPi Pin 6)
```

### 5.3 Digital Torch / Flashlight

```
  GPIO 22 (BCM) — RPi Pin 15
    │
   1 kΩ resistor
    │
   NPN transistor Base (e.g., 2N2222 / BC547)
   NPN Collector ──── Torch LED (+)
   NPN Emitter   ──── GND

  Torch LED (−) ──── GND
  Torch supply  ──── 3.3V or 5V depending on torch LED Vf
```

### 5.4 Passive Buzzer

```
  GPIO 18 (BCM) — RPi Pin 12 [hardware PWM0]
    │
   100Ω resistor
    │
   Buzzer (+) terminal
   Buzzer (-) terminal ──── GND (RPi Pin 6)
```

> GPIO 18 supports hardware PWM on RPi 5, giving cleaner tones than software PWM.

---

## 6. Raspberry Pi 5 Power Supply

Power RPi 5 from 2 × 3.7V LiPo cells via a **5V boost converter**:

```
2 × 3.7V LiPo in series → 7.4V
    │
  5V Boost Converter (e.g., MT3608 or XL6009)
    │
  USB-C PD adapter input (or direct 5.1V/5A output)
    │
  RPi 5 USB-C power port
```

> Minimum: 5.1V / 3A recommended for RPi 5. Use a quality boost converter.

---

## 7. Full Pin Reference Table

| RPi BCM GPIO | RPi Pin | Function | Connected To |
|:---:|:---:|---|---|
| 2 (SDA1) | 3 | I²C SDA | ADS1115 SDA, PCA9685 SDA |
| 3 (SCL1) | 5 | I²C SCL | ADS1115 SCL, PCA9685 SCL |
| 17 | 11 | Mode Switch Input | SPDT switch (pull-up) |
| 18 | 12 | Buzzer PWM | Passive buzzer (via 100Ω) |
| 22 | 15 | Torch GPIO | NPN transistor base (via 1kΩ) |
| 27 | 13 | Power LED | Green LED (via 330Ω) |
| — | 1 | 3.3V | ADS1115, PCA9685 logic, pull-ups |
| — | 6,9,14,20,25,30,34,39 | GND | All grounds (common rail) |

---

## 8. Elastic Return Mechanism

The fingers use **elastic bands (latex loops)** routed along the dorsal side  
of the hand structure. The servo closes the finger by pulling a tendon wire;  
the elastic band returns the finger to the open position when the servo relaxes.

- One 2mm latex band per finger (index, middle, ring, pinky)
- Route through guide rings at each phalanx
- Tension: finger should fully extend within 0.5 s when servo releases

---

## 9. Camera Placement

The **Raspberry Pi Camera 2** is mounted on the **palm face** of the prosthetic,  
pointing forward. This ensures the hand sees what it is about to pick up.

- Use the official 15-pin FFC ribbon cable (included with Camera 2)
- Connect to the **CAM/DISP 1** connector on RPi 5 (nearer the USB-C port)
- Camera field of view: ~84° diagonal

```bash
# Test camera
rpicam-still -o test.jpg
```

---

> For software setup, see [SETUP.md](SETUP.md)
