import RPi.GPIO as GPIO
import time


PAN_PIN  = 17
TILT_PIN = 27

PWM_FREQ    = 50
SERVO_MIN   = 2.5    # duty cycle % = 0 degrees
SERVO_MAX   = 12.5   # duty cycle % = 180 degrees
SERVO_MID   = 7.5    # duty cycle % = 90 degrees (center)

PAN_MIN_DEG  = 30
PAN_MAX_DEG  = 150
TILT_MIN_DEG = 45
TILT_MAX_DEG = 135

KP_PAN  = 0.035
KP_TILT = 0.030

DEADBAND_PX = 20


def degrees_to_duty(degrees):
    """Convert servo angle in degrees to PWM duty cycle."""
    return SERVO_MIN + (degrees / 180.0) * (SERVO_MAX - SERVO_MIN)


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


# ServoController class
class ServoController:

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(PAN_PIN,  GPIO.OUT)
        GPIO.setup(TILT_PIN, GPIO.OUT)

        self.pan_pwm  = GPIO.PWM(PAN_PIN,  PWM_FREQ)
        self.tilt_pwm = GPIO.PWM(TILT_PIN, PWM_FREQ)

        self.pan_pwm.start(SERVO_MID)
        self.tilt_pwm.start(SERVO_MID)

        # Current angles
        self.pan_deg  = 90.0
        self.tilt_deg = 90.0

        time.sleep(0.5)
        print("Servo controller initialized — centered at 90°/90°")

    def set_pan(self, degrees):
        degrees = clamp(degrees, PAN_MIN_DEG, PAN_MAX_DEG)
        self.pan_deg = degrees
        self.pan_pwm.ChangeDutyCycle(degrees_to_duty(degrees))

    def set_tilt(self, degrees):
        degrees = clamp(degrees, TILT_MIN_DEG, TILT_MAX_DEG)
        self.tilt_deg = degrees
        self.tilt_pwm.ChangeDutyCycle(degrees_to_duty(degrees))

    def center(self):
        self.set_pan(90)
        self.set_tilt(90)
        print("Servos centered")

    def update(self, err_x, err_y):
        """
        Proportional correction based on pixel error from frame center.
        Positive err_x = target right of center → pan right (increase angle)
        Positive err_y = target below center    → tilt down (decrease angle)
        """
        if abs(err_x) > DEADBAND_PX:
            self.pan_deg  += KP_PAN  * err_x
        if abs(err_y) > DEADBAND_PX:
            self.tilt_deg -= KP_TILT * err_y

        self.set_pan(self.pan_deg)
        self.set_tilt(self.tilt_deg)

    def cleanup(self):
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        GPIO.cleanup()
        print("GPIO cleaned up")


# Startup self-test
def servo_self_test(controller):
    """
    Sweep pan and tilt through their full range to verify
    mechanical freedom and confirm servo response before arming.
    """
    print("Running servo self-test...")
    SWEEP_DELAY = 0.02

    # Pan sweep
    for angle in range(90, PAN_MAX_DEG, 2):
        controller.set_pan(angle)
        time.sleep(SWEEP_DELAY)
    for angle in range(PAN_MAX_DEG, PAN_MIN_DEG, -2):
        controller.set_pan(angle)
        time.sleep(SWEEP_DELAY)
    for angle in range(PAN_MIN_DEG, 90, 2):
        controller.set_pan(angle)
        time.sleep(SWEEP_DELAY)

    # Tilt sweep
    for angle in range(90, TILT_MAX_DEG, 2):
        controller.set_tilt(angle)
        time.sleep(SWEEP_DELAY)
    for angle in range(TILT_MAX_DEG, TILT_MIN_DEG, -2):
        controller.set_tilt(angle)
        time.sleep(SWEEP_DELAY)
    for angle in range(TILT_MIN_DEG, 90, 2):
        controller.set_tilt(angle)
        time.sleep(SWEEP_DELAY)

    controller.center()
    print("Servo self-test passed")
    return True


if __name__ == "__main__":
    ctrl = ServoController()
    try:
        servo_self_test(ctrl)
        print(f"Pan: {ctrl.pan_deg:.1f}°  Tilt: {ctrl.tilt_deg:.1f}°")
    finally:
        ctrl.cleanup()
