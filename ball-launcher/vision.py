import cv2
import numpy as np
import time

TARGET_HSV_LOWER = np.array([10,  120, 100])
TARGET_HSV_UPPER = np.array([25,  255, 255])

MIN_CONTOUR_AREA = 500

FRAME_W = 640
FRAME_H = 480
FRAME_CX = FRAME_W // 2
FRAME_CY = FRAME_H // 2

DEADBAND_PX = 20

# Target detection
def detect_target(frame):

    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv     = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask    = cv2.inRange(hsv, TARGET_HSV_LOWER, TARGET_HSV_UPPER)

    # Morphological cleanup
    mask = cv2.erode(mask,  None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Take the largest contour above minimum area
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
        return None

    (cx, cy), radius = cv2.minEnclosingCircle(largest)
    return int(cx), int(cy), int(radius)


# Error calculation — offset from frame center
def compute_error(cx, cy):
    """
    Compute pixel error between detected target and frame center.

    Returns:
        (err_x, err_y) — positive x = target is right of center
                        — positive y = target is below center
    """
    err_x = cx - FRAME_CX
    err_y = cy - FRAME_CY
    return err_x, err_y


# Annotate frame for debugging
def annotate_frame(frame, cx, cy, radius, err_x, err_y, locked):
    cv2.circle(frame, (cx, cy), radius, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
    cv2.line(frame, (FRAME_CX, 0), (FRAME_CX, FRAME_H), (255, 255, 0), 1)
    cv2.line(frame, (0, FRAME_CY), (FRAME_W, FRAME_CY), (255, 255, 0), 1)

    status = "LOCKED" if locked else "TRACKING"
    color  = (0, 255, 0) if locked else (0, 165, 255)
    cv2.putText(frame, f"{status}  err=({err_x},{err_y})",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return frame


# Main vision loop
def run_vision(preview=False):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

    print("Vision system started. Press Ctrl+C to stop.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera read failed — retrying...")
                time.sleep(0.1)
                continue

            result = detect_target(frame)

            if result is None:
                yield None, None, False
                if preview:
                    cv2.putText(frame, "NO TARGET", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow("RailVision Launcher", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                continue

            cx, cy, radius = result
            err_x, err_y   = compute_error(cx, cy)
            locked = abs(err_x) <= DEADBAND_PX and abs(err_y) <= DEADBAND_PX

            yield err_x, err_y, locked

            if preview:
                frame = annotate_frame(frame, cx, cy, radius, err_x, err_y, locked)
                cv2.imshow("Launcher Targeting", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    finally:
        cap.release()
        if preview:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    for err_x, err_y, locked in run_vision(preview=True):
        if err_x is not None:
            print(f"err_x={err_x:+4d}  err_y={err_y:+4d}  {'[LOCKED]' if locked else ''}")
