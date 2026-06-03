import serial
import csv
import time
import argparse
from datetime import datetime

BAUD_RATE   = 115200
COLUMNS     = ["timestamp_ms", "voltage_V", "current_A",
               "accel_x_g", "accel_y_g", "accel_z_g",
               "gyro_x_ds", "gyro_y_ds", "gyro_z_ds"]

def main(args):
    port   = args.port
    output = args.output or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    print(f"Connecting to {port} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=2)
        time.sleep(2)  
        print(f"Connected. Logging to {output}\n")

        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)

            row_count = 0
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()

                if not line or line.startswith("=") or line.startswith(" ") or line.startswith("["):
                    if line:
                        print(line)
                    continue

                parts = line.split(",")
                if len(parts) == len(COLUMNS):
                    try:
                        row = [float(p) for p in parts]
                        writer.writerow(row)
                        row_count += 1

                        if row_count % 50 == 0:
                            print(f"  [{row_count} rows] "
                                  f"V={row[1]:.2f}V  "
                                  f"I={row[2]:.3f}A  "
                                  f"ax={row[3]:.2f}g")
                    except ValueError:
                        pass

    except KeyboardInterrupt:
        print(f"\nLogging stopped. {row_count} rows saved to {output}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RC car serial data logger")
    parser.add_argument("--port",   required=True,  help="Serial port (e.g. /dev/ttyUSB0 or COM3)")
    parser.add_argument("--output", required=False, help="Output CSV filename")
    args = parser.parse_args()
    main(args)
