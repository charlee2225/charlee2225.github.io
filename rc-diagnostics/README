# RC Car Pit Crew Diagnostics Console

**Rutgers University ECE**
September – November 2025

An Arduino Nano-based pre-run diagnostics console that validates RC car system health before operation. Runs five structured checks on power-on and arms or locks the system based on results. Detected 8 of 10 injected failure cases before operation during validation testing.

---

## System Overview

On power-on, the system runs five sequential diagnostic checks:

| Check | What it validates |
|-------|------------------|
| I2C bus scan | Verifies INA219 and MPU-6050 are detected on the bus |
| Battery voltage | Confirms voltage is within safe operating range (6.5V – 12.6V) |
| Battery current | Confirms idle current draw is within limits |
| IMU health | Validates MPU-6050 connectivity and accelerometer data at rest |
| Motor driver | Applies brief PWM pulse and confirms measurable current response |

If all checks pass the system arms and begins continuous telemetry logging. If any check fails the system locks and blinks the status LED.

---

## Files

| File | Description |
|------|-------------|
| `rc_diagnostics.ino` | Arduino Nano firmware — startup checks and telemetry loop |
| `logger.py` | Python serial logger — captures CSV telemetry for post-run analysis |

---

## Hardware

- Arduino Nano
- INA219 current/voltage sensor (I2C 0x40)
- MPU-6050 IMU (I2C 0x68)
- RC motor driver (PWM on D9)
- Status LED (D13) and Ready LED (D12)
- 2S/3S LiPo battery

---

## Usage

**Flash firmware:**
Upload `rc_diagnostics.ino` to Arduino Nano using Arduino IDE.

**Monitor diagnostics:**
Open Serial Monitor at 115200 baud to view startup check results.

**Log telemetry to CSV:**
```bash
python logger.py --port /dev/ttyUSB0 --output run_001.csv
```

On Windows use `--port COM3` (or whichever port the Nano is on).

---

## Telemetry Output Format

The firmware streams CSV-formatted data at 10Hz after arming:

```
timestamp_ms, voltage_V, current_A, accel_x_g, accel_y_g, accel_z_g, gyro_x_ds, gyro_y_ds, gyro_z_ds
1234, 7.42, 0.312, 0.021, -0.015, 0.998, 0.12, -0.08, 0.03
```

---

## Results

| Metric | Value |
|--------|-------|
| Injected failure cases | 10 |
| Detected before operation | 8 |
| Detection rate | 80% |

Failure cases tested included low battery voltage, disconnected IMU, motor driver open circuit, I2C bus fault, and overcurrent conditions.

---

## Dependencies

**Arduino:**
- `Adafruit_INA219` library
- `MPU6050` library (jrowberg/i2cdevlib)
- `Wire.h` (built-in)

**Python:**
```bash
pip install pyserial
```
