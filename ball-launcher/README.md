# Camera-Assisted Ball Launch Platform

January – March 2026

A vision-guided embedded targeting platform that uses OpenCV color segmentation to detect a target and drive pan/tilt servos to center a dual-flywheel ball launcher. Improved targeting accuracy from 56% to 82% across 30 trials through iterative tuning of the vision-guided control loop.

---

## System Overview

```
Camera → OpenCV Detection → Error Calculation → Servo P-Controller → Pan/Tilt Mount
                                                                           ↓
                                                              Lock confirmed → Fire flywheels
```

**Hardware:**
- Raspberry Pi 4B (vision + control)
- Raspberry Pi Camera Module v2
- 2x hobby servos (pan and tilt)
- Dual flywheel launcher (PWM speed control)
- 3D printed housing and mount

---

## Files

| File | Description |
|------|-------------|
| `main.py` | Main controller - startup checks, trial loop, data logging |
| `vision.py` | OpenCV target detection and error computation |
| `servo_control.py` | Pan/tilt servo PWM control and self-test sweep |

---

## Key Features

**Startup self-test:** Before arming, the system runs a three-point check: servo range sweep, camera availability, and flywheel GPIO validation. The system will not arm if any check fails.

**Safety interlocks:** The flywheel only spins up once the target is locked within the deadband. A minimum lock hold time prevents premature firing on transient detections.

**Data logging:** Every trial logs fired status, hit/miss result, targeting latency, and elapsed time to a CSV file for post-session analysis.

---

## Usage

```bash
# Run 30 trials and log to results.csv
python main.py --trials 30 --log results.csv

# Test vision system only (with preview window)
python vision.py

# Test servo sweep only
python servo_control.py
```

---

## Results

| Metric | Value |
|--------|-------|
| Trials run | 30 |
| Initial accuracy | 56% |
| Final accuracy | 82% |
| Improvement | +26 percentage points |

Accuracy improvement was achieved through iterative tuning of the proportional gain constants `KP_PAN` and `KP_TILT`, deadband threshold, and lock hold time.

---

## Dependencies

```
opencv-python
RPi.GPIO
numpy
```

Install with:
```bash
pip install opencv-python numpy
```
