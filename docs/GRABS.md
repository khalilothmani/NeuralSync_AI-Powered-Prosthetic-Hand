# 🤚 NeuralSync — Grip Profiles

## Overview

The NeuralSync hand implements **5 distinct grip profiles**, each optimised for  
a different object class. All grips use smooth servo interpolation to avoid  
jolting fragile objects or dropping heavy ones.

---

## Servo Tick Reference

The PCA9685 generates PWM at 50Hz. Each period = 20ms = 4096 ticks.

| Tick Value | Pulse Width | Servo Angle (approx.) | State |
|:----------:|:-----------:|:---------------------:|-------|
| 102 | ~500 µs | 0° | Fully Open |
| 204 | ~1000 µs | 45° | Mid-Open |
| 307 | ~1500 µs | 90° | Neutral |
| 409 | ~2000 µs | 135° | Mid-Close |
| 512 | ~2500 µs | 180° | Fully Closed |

> Adjust limits in `config/config.yaml` if your servos have a different range.

---

## Grab 0 — RELEASE (Open Hand)

> **Default resting state. Activated on second EMG trigger or mode change.**

| Channel | Finger | Ticks | Angle | Position |
|:-------:|--------|:-----:|:-----:|---------|
| 0 | Index flex | 102 | 0° | Fully Open |
| 1 | Middle flex | 102 | 0° | Fully Open |
| 2 | Ring flex | 102 | 0° | Fully Open |
| 3 | Pinky flex | 102 | 0° | Fully Open |
| 4 | Thumb rotation | 102 | 0° | Abducted |
| 5 | Thumb flex | 102 | 0° | Open |

**Motion speed**: 0.008 s/tick (fast — instant release for safety)

**Use case**: Default position. Always return here between grabs.

---

## Grab 1 — POWER (Cylindrical / Hard Grip)

> **Used in Mode 1 (Normal) and for MEDIUM/HEAVY category objects in Mode 2.**

| Channel | Finger | Ticks | Angle | Position |
|:-------:|--------|:-----:|:-----:|---------|
| 0 | Index flex | 512 | 180° | Fully Closed |
| 1 | Middle flex | 512 | 180° | Fully Closed |
| 2 | Ring flex | 512 | 180° | Fully Closed |
| 3 | Pinky flex | 512 | 180° | Fully Closed |
| 4 | Thumb rotation | 409 | 135° | Opposed |
| 5 | Thumb flex | 409 | 135° | Mid-Close |

**Motion speed**: 0.006 s/tick (fast — confident grip)

**Use case**: Water bottles, tools, jars, books, cylindrical objects.

---

## Grab 2 — SENSITIVE (Soft Partial)

> **Used for fragile/crushable objects (eggs, glasses, ornaments).**

| Channel | Finger | Ticks | Angle | Position |
|:-------:|--------|:-----:|:-----:|---------|
| 0 | Index flex | 204 | 45° | Mid-Open |
| 1 | Middle flex | 204 | 45° | Mid-Open |
| 2 | Ring flex | 204 | 45° | Mid-Open |
| 3 | Pinky flex | 204 | 45° | Mid-Open |
| 4 | Thumb rotation | 307 | 90° | Neutral |
| 5 | Thumb flex | 204 | 45° | Mid-Open |

**Motion speed**: 0.012 s/tick (**slowest — maximally gentle**)

**Use case**: Eggs, wine glasses, ornaments, thin chips, flowers.

---

## Grab 3 — LIGHT (Gentle Cylindrical)

> **Used for lightweight objects that need a secure but non-crushing grip.**

| Channel | Finger | Ticks | Angle | Position |
|:-------:|--------|:-----:|:-----:|---------|
| 0 | Index flex | 409 | 135° | Mid-Close |
| 1 | Middle flex | 409 | 135° | Mid-Close |
| 2 | Ring flex | 409 | 135° | Mid-Close |
| 3 | Pinky flex | 307 | 90° | Neutral |
| 4 | Thumb rotation | 307 | 90° | Neutral |
| 5 | Thumb flex | 307 | 90° | Neutral |

**Motion speed**: 0.008 s/tick (medium)

**Use case**: Pen, apple, fruit, paper cup, TV remote, phone.

---

## Grab 4 — PINCH (Two-Finger)

> **Used for small flat or thin objects requiring precision.**

| Channel | Finger | Ticks | Angle | Position |
|:-------:|--------|:-----:|:-----:|---------|
| 0 | Index flex | 409 | 135° | Mid-Close |
| 1 | Middle flex | 102 | 0° | Fully Open |
| 2 | Ring flex | 102 | 0° | Fully Open |
| 3 | Pinky flex | 102 | 0° | Fully Open |
| 4 | Thumb rotation | 512 | 180° | Fully Opposed |
| 5 | Thumb flex | 409 | 135° | Mid-Close |

**Motion speed**: 0.010 s/tick

**Use case**: Coins, keys, cards, small electronics, pills, screws.

---

## Elastic Return Mechanism

- Each finger has one **latex elastic band** routed along the dorsal side
- The servo tendon (wire/cord) runs through palmar guide rings
- Servo **closes** the finger by pulling the tendon
- Servo **relaxes** → elastic band returns finger to open position
- **Thumb rotation** servo uses dual tendons (no elastic needed for opposition axis)

### Elastic Band Sizing
| Finger | Band length (relaxed) | Band cross-section |
|--------|-----------------------|--------------------|
| Index | 60–70 mm | 2mm circular |
| Middle | 65–75 mm | 2mm circular |
| Ring | 60–70 mm | 2mm circular |
| Pinky | 55–65 mm | 2mm circular |

---

## Buzzer Feedback per Grab

| Grab | Sound Pattern | Frequency |
|------|-------------|-----------|
| RELEASE | Single low beep | 330 Hz / 300ms |
| POWER (Mode 1) | Single mid beep | 523 Hz / 200ms |
| SENSITIVE | Two gentle beeps | 330 Hz × 2 |
| LIGHT | Single tone | 440 Hz / 150ms |
| MEDIUM → POWER | Single mid beep | 523 Hz / 200ms |
| HEAVY → POWER | Deep beep | 659 Hz / 250ms |
| PINCH | Rising double | 880+1046 Hz |
| Error | Three harsh buzzes | 200 Hz × 3 |
