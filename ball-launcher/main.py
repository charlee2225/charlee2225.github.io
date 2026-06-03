import time
import csv
import argparse
import RPi.GPIO as GPIO
from vision import run_vision, DEADBAND_PX
from servo_control import ServoController, servo_self_test

# PWM speed control 
FLYWHEEL_PIN   = 22
FLYWHEEL_FREQ  = 50
FLYWHEEL_IDLE  = 0.0    # duty cycle % when idle
FLYWHEEL_SPEED = 8.5    # duty cycle % at launch speed

LOCK_HOLD_TIME = 0.4

TRIAL_TIMEOUT  = 10.0

TRIAL_COOLDOWN = 2.0


# Startup self-test
def run_startup_checks(controller):
    print("\n=== STARTUP SELF-TEST ===")
    checks = {}

    # Check 1 — servo sweep
    print("[1/3] Servo range check...")
    checks["servo_sweep"] = servo_self_test(controller)

    # Check 2 — camera availability
    print("[2/3] Camera check...")
    import cv2
    cap = cv2.VideoCapture(0)
    ret, _ = cap.read()
    cap.release()
    checks["camera"] = ret
    print(f"      Camera: {'OK' if ret else 'FAIL'}")

    # Check 3 — flywheel GPIO
    print("[3/3] Flywheel GPIO check...")
    try:
        GPIO.setup(FLYWHEEL_PIN, GPIO.OUT)
        fw = GPIO.PWM(FLYWHEEL_PIN, FLYWHEEL_FREQ)
        fw.start(FLYWHEEL_IDLE)
        time.sleep(0.2)
        fw.stop()
        checks["flywheel"] = True
        print("      Flywheel: OK")
    except Exception as e:
        checks["flywheel"] = False
        print(f"      Flywheel: FAIL ({e})")

    all_passed = all(checks.values())
    print(f"\nSelf-test result: {'PASS — system armed' if all_passed else 'FAIL — system locked'}")
    print("=========================\n")
    return all_passed, checks


# Flywheel control
def spin_up(fw_pwm):
    fw_pwm.ChangeDutyCycle(FLYWHEEL_SPEED)
    time.sleep(0.3)  # spin-up delay

def spin_down(fw_pwm):
    fw_pwm.ChangeDutyCycle(FLYWHEEL_IDLE)


# Single trial — track, lock, fire
def run_trial(controller, fw_pwm, trial_num):
    print(f"Trial {trial_num:02d} — searching for target...")
    start_time  = time.time()
    lock_start  = None
    hit         = False
    fired       = False
    latency_ms  = None

    for err_x, err_y, locked in run_vision(preview=False):
        elapsed = time.time() - start_time

        # Timeout
        if elapsed > TRIAL_TIMEOUT:
            print(f"  Trial {trial_num:02d} TIMEOUT after {elapsed:.1f}s")
            break

        if err_x is None:
            lock_start = None
            spin_down(fw_pwm)
            continue

        # Update servo position
        controller.update(err_x, err_y)

        if locked:
            if lock_start is None:
                lock_start = time.time()
                spin_up(fw_pwm)
                print(f"  Target locked — spinning up flywheels...")

            hold_time = time.time() - lock_start

            if hold_time >= LOCK_HOLD_TIME and not fired:
                # Fire
                latency_ms = (time.time() - start_time) * 1000
                print(f"  FIRE at {hold_time:.2f}s hold | latency={latency_ms:.0f}ms")
                fired = True
                time.sleep(0.5)
                spin_down(fw_pwm)
                # Prompt for hit/miss
                result = input("  Hit? (y/n): ").strip().lower()
                hit = result == "y"
                break
        else:
            lock_start = None
            spin_down(fw_pwm)

    return {
        "trial":      trial_num,
        "fired":      fired,
        "hit":        hit,
        "latency_ms": round(latency_ms, 1) if latency_ms else None,
        "elapsed_s":  round(time.time() - start_time, 2)
    }



def main(args):
    GPIO.setmode(GPIO.BCM)
    controller = ServoController()

    # Startup checks — safety interlock
    passed, checks = run_startup_checks(controller)
    if not passed:
        print("Startup checks failed. Resolve faults before proceeding.")
        controller.cleanup()
        return

    # Flywheel PWM
    GPIO.setup(FLYWHEEL_PIN, GPIO.OUT)
    fw_pwm = GPIO.PWM(FLYWHEEL_PIN, FLYWHEEL_FREQ)
    fw_pwm.start(FLYWHEEL_IDLE)

    results = []
    hits    = 0

    try:
        for trial in range(1, args.trials + 1):
            result = run_trial(controller, fw_pwm, trial)
            results.append(result)
            if result["hit"]:
                hits += 1

            accuracy = hits / trial * 100
            print(f"  Result: {'HIT' if result['hit'] else 'MISS'} | "
                  f"Running accuracy: {accuracy:.1f}% ({hits}/{trial})\n")

            controller.center()
            time.sleep(TRIAL_COOLDOWN)

    finally:
        fw_pwm.stop()
        controller.cleanup()

    # Summary
    final_accuracy = hits / len(results) * 100 if results else 0
    print(f"\n=== RESULTS ===")
    print(f"Trials:   {len(results)}")
    print(f"Hits:     {hits}")
    print(f"Accuracy: {final_accuracy:.1f}%")

    # Save to CSV
    if args.log and results:
        with open(args.log, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to: {args.log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ball launcher main controller")
    parser.add_argument("--trials", type=int, default=10,  help="Number of trials to run")
    parser.add_argument("--log",    type=str, default="results.csv", help="Output CSV path")
    args = parser.parse_args()
    main(args)
