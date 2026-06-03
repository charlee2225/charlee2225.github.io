#include <Wire.h>
#include <Adafruit_INA219.h>
#include <MPU6050.h>

// Pin assignments
#define MOTOR_PWM_PIN   9
#define STATUS_LED_PIN  13
#define READY_LED_PIN   12   // Green = armed, Red = fault

// Thresholds
#define BATT_VOLTAGE_MIN     6.5f    // V  — minimum acceptable battery voltage
#define BATT_VOLTAGE_MAX    12.6f    // V  — maximum (full charge 3S LiPo)
#define BATT_CURRENT_MAX     5.0f    // A  — max idle current draw
#define MOTOR_PWM_TEST_VAL   80      // 0-255 PWM for motor driver response test
#define MOTOR_RESPONSE_DELAY 200     // ms to wait for motor driver response
#define IMU_ACCEL_MIN       -2.0f    // g  — min plausible accel reading
#define IMU_ACCEL_MAX        2.0f    // g  — max plausible accel reading (at rest)

// I2C addresses
#define INA219_ADDR  0x40
#define MPU6050_ADDR 0x68

Adafruit_INA219 ina219(INA219_ADDR);
MPU6050 mpu(MPU6050_ADDR);

struct DiagResult {
  bool battery_voltage;
  bool battery_current;
  bool imu_connected;
  bool imu_data_valid;
  bool motor_driver;
  bool i2c_bus;
};

// Pass/fail
void printResult(const char* label, bool passed) {
  Serial.print("  [");
  Serial.print(passed ? "PASS" : "FAIL");
  Serial.print("] ");
  Serial.println(label);
}

// Check 1 — I2C bus scan
bool checkI2CBus() {
  Serial.println("\n[1/5] I2C Bus Scan");
  int deviceCount = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("      Device found at 0x");
      Serial.println(addr, HEX);
      deviceCount++;
    }
  }
  bool passed = (deviceCount >= 2); 
  printResult("I2C bus", passed);
  return passed;
}

// Check 2 — Battery voltage and current
bool checkBattery(float &voltage_out, float &current_out) {
  Serial.println("\n[2/5] Battery Health");

  if (!ina219.begin()) {
    Serial.println("      INA219 init failed");
    return false;
  }

  float voltage = ina219.getBusVoltage_V();
  float current = ina219.getCurrent_mA() / 1000.0f;  
  float power   = ina219.getPower_mW();

  Serial.print("      Voltage: "); Serial.print(voltage, 2); Serial.println(" V");
  Serial.print("      Current: "); Serial.print(current, 3); Serial.println(" A");
  Serial.print("      Power:   "); Serial.print(power,   1); Serial.println(" mW");

  voltage_out = voltage;
  current_out = current;

  bool volt_ok    = (voltage >= BATT_VOLTAGE_MIN && voltage <= BATT_VOLTAGE_MAX);
  bool current_ok = (current <= BATT_CURRENT_MAX);

  printResult("Battery voltage", volt_ok);
  printResult("Battery current", current_ok);

  return volt_ok && current_ok;
}

// Check 3 — IMU connectivity and data validity
bool checkIMU() {
  Serial.println("\n[3/5] IMU Health (MPU-6050)");

  mpu.initialize();
  bool connected = mpu.testConnection();
  printResult("MPU-6050 connection", connected);

  if (!connected) return false;

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  float ax_g = ax / 16384.0f;
  float ay_g = ay / 16384.0f;
  float az_g = az / 16384.0f;

  Serial.print("      Accel (g): ");
  Serial.print(ax_g, 3); Serial.print(", ");
  Serial.print(ay_g, 3); Serial.print(", ");
  Serial.println(az_g, 3);

  float mag = sqrt(ax_g*ax_g + ay_g*ay_g + az_g*az_g);
  Serial.print("      Magnitude: "); Serial.print(mag, 3); Serial.println(" g");

  bool data_valid = (mag > 0.8f && mag < 1.2f);
  printResult("IMU data valid (at rest)", data_valid);

  return data_valid;
}

// Check 4 — Motor driver response
bool checkMotorDriver() {
  Serial.println("\n[4/5] Motor Driver Response");

  float baseline_current = ina219.getCurrent_mA() / 1000.0f;

  analogWrite(MOTOR_PWM_PIN, MOTOR_PWM_TEST_VAL);
  delay(MOTOR_RESPONSE_DELAY);
  float active_current = ina219.getCurrent_mA() / 1000.0f;
  analogWrite(MOTOR_PWM_PIN, 0);

  float delta = active_current - baseline_current;

  Serial.print("      Baseline current: "); Serial.print(baseline_current, 3); Serial.println(" A");
  Serial.print("      Active current:   "); Serial.print(active_current,   3); Serial.println(" A");
  Serial.print("      Delta:            "); Serial.print(delta,            3); Serial.println(" A");

  bool responded = (delta > 0.05f);
  printResult("Motor driver response", responded);

  return responded;
}

// Check 5 — UART loopback
bool checkUART() {
  Serial.println("\n[5/5] UART Check");
  bool uart_ok = Serial.availableForWrite() > 0;
  printResult("UART (hardware serial)", uart_ok);
  return uart_ok;
}

// Print summary and arm/fault decision
void printSummary(DiagResult &r, float voltage, float current) {
  Serial.println("\n=============================");
  Serial.println("    DIAGNOSTICS SUMMARY");
  Serial.println("=============================");
  Serial.print("Battery voltage:  "); Serial.println(r.battery_voltage  ? "PASS" : "FAIL");
  Serial.print("Battery current:  "); Serial.println(r.battery_current  ? "PASS" : "FAIL");
  Serial.print("IMU connected:    "); Serial.println(r.imu_connected    ? "PASS" : "FAIL");
  Serial.print("IMU data valid:   "); Serial.println(r.imu_data_valid   ? "PASS" : "FAIL");
  Serial.print("Motor driver:     "); Serial.println(r.motor_driver     ? "PASS" : "FAIL");
  Serial.print("I2C bus:          "); Serial.println(r.i2c_bus          ? "PASS" : "FAIL");
  Serial.println("-----------------------------");

  bool all_passed = r.battery_voltage && r.battery_current &&
                    r.imu_connected   && r.imu_data_valid  &&
                    r.motor_driver    && r.i2c_bus;

  if (all_passed) {
    Serial.println("STATUS: ALL CHECKS PASSED");
    Serial.print("Battery: "); Serial.print(voltage, 2);
    Serial.print("V  |  Current: "); Serial.print(current, 3); Serial.println("A");
    Serial.println("System ARMED — ready to run");
    digitalWrite(READY_LED_PIN, HIGH);
  } else {
    Serial.println("STATUS: FAULT DETECTED");
    Serial.println("System LOCKED — resolve faults before operation");
    // Blink status LED to indicate fault
    for (int i = 0; i < 6; i++) {
      digitalWrite(STATUS_LED_PIN, HIGH);
      delay(200);
      digitalWrite(STATUS_LED_PIN, LOW);
      delay(200);
    }
  }
  Serial.println("=============================\n");
}

// Setup — run diagnostics once on power-on
void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(READY_LED_PIN,  OUTPUT);
  pinMode(MOTOR_PWM_PIN,  OUTPUT);

  digitalWrite(STATUS_LED_PIN, HIGH); 

  Serial.println("\n==============================");
  Serial.println("  RC CAR DIAGNOSTICS CONSOLE");
  Serial.println("  Rutgers ECE · Nov 2025");
  Serial.println("==============================");
  Serial.println("Running pre-run checks...");

  DiagResult result;
  float voltage = 0, current = 0;

  result.i2c_bus        = checkI2CBus();
  bool batt_ok          = checkBattery(voltage, current);
  result.battery_voltage = batt_ok;
  result.battery_current = batt_ok;
  bool imu_ok           = checkIMU();
  result.imu_connected  = imu_ok;
  result.imu_data_valid = imu_ok;
  result.motor_driver   = checkMotorDriver();
  result.i2c_bus        = checkUART();

  printSummary(result, voltage, current);

  digitalWrite(STATUS_LED_PIN, LOW);
}

// Loop — continuous IMU monitoring after armed
void loop() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  float ax_g = ax / 16384.0f;
  float ay_g = ay / 16384.0f;
  float az_g = az / 16384.0f;
  float gx_ds = gx / 131.0f;
  float gy_ds = gy / 131.0f;
  float gz_ds = gz / 131.0f;

  float batt_v = ina219.getBusVoltage_V();
  float batt_a = ina219.getCurrent_mA() / 1000.0f;

  Serial.print(millis()); Serial.print(",");
  Serial.print(batt_v, 3); Serial.print(",");
  Serial.print(batt_a, 3); Serial.print(",");
  Serial.print(ax_g, 3);   Serial.print(",");
  Serial.print(ay_g, 3);   Serial.print(",");
  Serial.print(az_g, 3);   Serial.print(",");
  Serial.print(gx_ds, 2);  Serial.print(",");
  Serial.print(gy_ds, 2);  Serial.print(",");
  Serial.println(gz_ds, 2);

  delay(100);  // 10Hz logging rate
}
