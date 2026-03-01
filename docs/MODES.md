# 🔄 NeuralSync — Operating Modes

## Mode Selection

A physical **SPDT toggle switch** connected to GPIO 17 selects the mode:

| Switch Position | GPIO 17 State | Active Mode |
|:---------------:|:-------------:|------------|
| LEFT (open) | HIGH (pull-up) | Mode 1 — Normal |
| RIGHT (ground) | LOW | Mode 2 — AI Vision |

The mode is checked at ~50 Hz in the main loop. Switching modes mid-grip  
immediately triggers a release (Grab 0) before entering the new mode.

---

## Mode 1 — Normal Mode 💪

Simple toggle behaviour: first EMG trigger grabs, second releases.

```
┌─────────────────────────────────────────────────────────────────┐
│                     MODE 1 — NORMAL MODE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    START                                                        │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────┐        EMG > threshold?         ┌──────────────┐  │
│  │  IDLE   │──────────── YES ───────────────►│  GRAB 1      │  │
│  │  (open) │                                 │  POWER GRAB  │  │
│  └─────────┘                                 └──────┬───────┘  │
│       ▲                                             │          │
│       │               EMG > threshold?              │          │
│       └──────────────── YES ◄──────────────── GRABBING state   │
│                                                                 │
│  Grab 0 (RELEASE) executed → back to IDLE                      │
└─────────────────────────────────────────────────────────────────┘
```

### Flow in detail

1. System powers on → hand opens (Grab 0) → green LED on → buzzer plays `system_on`
2. Loop monitors EMG at 50Hz
3. **IDLE state**: EMG spike ≥ threshold → execute **Grab 1 (POWER)**
   - Buzzer: `grab_medium` (523 Hz beep)
   - Transitions to **GRABBING** state
4. **GRABBING state**: any further EMG spike → execute **Grab 0 (RELEASE)**
   - Buzzer: `release` (330 Hz)
   - Returns to **IDLE** state
5. A 1-second cooldown prevents double-triggering

### Usage tips
- Contract your forearm muscle firmly for ~0.3s to trigger
- Wait for the buzzer confirmation before attempting the grip
- One more firm contraction while gripping → release

---

## Mode 2 — AI Vision Mode 🤖

Object-aware adaptive gripping using the onboard camera and YOLOv11x.

```
┌──────────────────────────────────────────────────────────────────────┐
│                      MODE 2 — AI VISION MODE                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    START                                                             │
│      │                                                               │
│      ▼                                                               │
│  ┌─────────┐                                                         │
│  │  IDLE   │                                                         │
│  │  (open) │                                                         │
│  └────┬────┘                                                         │
│       │ EMG > threshold                                              │
│       ▼                                                              │
│  ┌────────────────┐                                                  │
│  │ Flash Torch ON │  (GPIO 22 HIGH — 120ms before capture)           │
│  └────────┬───────┘                                                  │
│           │                                                          │
│           ▼                                                          │
│  ┌────────────────┐                                                  │
│  │ Capture Frame  │  (discard 5 warmup frames → grab 1 JPEG)         │
│  └────────┬───────┘                                                  │
│           │                                                          │
│           ▼                                                          │
│  ┌────────────────┐                                                  │
│  │ Torch OFF      │                                                  │
│  └────────┬───────┘                                                  │
│           │                                                          │
│           ▼                                                          │
│  ┌────────────────────┐                                              │
│  │ YOLO Inference     │  (conf=0.35, iou=0.45)                       │
│  │ yolo11x.pt         │                                              │
│  └────────┬───────────┘                                              │
│           │                                                          │
│    ┌──────┴──────┐                                                   │
│    │             │                                                   │
│  Object       No object / unknown                                    │
│  detected     ────────────────────────────────────────►              │
│    │                                           ┌───────────────┐     │
│    ▼                                           │ ERROR BUZZER  │     │
│  ┌──────────────────────────────────┐          │ (3× 200Hz)    │     │
│  │ Classify:                        │          └───────┬───────┘     │
│  │  SENSITIVE → Grab 2              │                  │             │
│  │  LIGHT     → Grab 3              │          Return to IDLE        │
│  │  MEDIUM    → Grab 1              │          (wait next trigger)   │
│  │  HEAVY     → Grab 1              │                                │
│  │  PINCH     → Grab 4              │                                │
│  └────────────┬─────────────────────┘                               │
│               │                                                      │
│               ▼                                                      │
│  ┌──────────────────┐                                                │
│  │ Execute Grab N   │                                                │
│  │ + Buzzer confirm │                                                │
│  └─────────┬────────┘                                               │
│             │                                                        │
│             ▼                                                        │
│         GRABBING state                                               │
│             │ EMG > threshold                                        │
│             ▼                                                        │
│  ┌──────────────────┐                                                │
│  │ RELEASE (Grab 0) │                                                │
│  └─────────┬────────┘                                               │
│             │                                                        │
│             ▼                                                        │
│           IDLE                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Flow in detail

1. **IDLE** — hand is open, system monitors EMG
2. **EMG spike** above threshold triggers the capture sequence
3. **Torch** (GPIO 22) turns ON; 120ms pause for LED stabilisation
4. Camera discards 5 warm-up frames (auto-exposure adjustment)
5. **Single JPEG** is saved to `captured_frame.jpg`
6. **Torch** turns OFF
7. **YOLOv11x** runs inference on the JPEG
8. Highest-confidence detection label is matched to a category:

| Category | Objects (examples) | Grab |
|----------|-------------------|------|
| SENSITIVE | Egg, wine glass, ornament | Grab 2 |
| LIGHT | Pen, apple, remote, mug | Grab 3 |
| MEDIUM | Bottle (small), book, phone | Grab 1 |
| HEAVY | Water bottle 1L+, dumbbell | Grab 1 |
| PINCH | Coin, key, credit card, pill | Grab 4 |

9. **Recognised** → execute grab, play category-specific buzzer sound
10. **Not recognised** → three error buzzes, return to IDLE, try again
11. Second **EMG spike** while gripping → RELEASE

### Usage tips
- Hold the object in front of the camera (palm-forward view)
- The torch illuminates the object for cleaner detection
- If detection fails repeatedly, try different lighting or angle
- Add custom objects to the lists in `src/object_classifier.py`

---

## Mode Switching During Operation

| Situation | Result |
|-----------|--------|
| Switch mode while **IDLE** | Buzzer announces new mode, continues normally |
| Switch mode while **GRABBING** | Immediate RELEASE → new mode announced |
| Brief switch bounce | Debounced by 50Hz polling (no spurious transitions) |

---

## System Startup Sequence

```
1. GPIO setup (switch, LED, buzzer, torch)
2. Power LED → ON  (green light)
3. Buzzer → "system_on" (two ascending tones)
4. Check switch position → determine initial mode
5. Buzzer → "mode_1" or "mode_2" announcement
6. ServoController → open hand (Grab 0)
7. Main loop starts (50Hz EMG polling)
```

## System Shutdown (Ctrl+C or SIGTERM)

```
1. Stop main loop
2. Execute RELEASE (Grab 0)  ← safety first
3. Servo controller → deinit PCA9685
4. Camera → release V4L2 device
5. Buzzer → close GPIO PWM
6. Power LED → OFF
7. GPIO cleanup → all pins to safe state
8. Exit
```
