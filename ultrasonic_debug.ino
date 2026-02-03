#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

// ===== PINS (NodeMCU ESP8266) =====
const uint8_t SDA_PIN  = D2;
const uint8_t SCL_PIN  = D1;
const int     TRIG_PIN = D3;
const int     ECHO_PIN = D4;

// ===== LCD =====
hd44780_I2Cexp lcd;

// ===== Ultrasonic Settings =====
const unsigned long ULTRASONIC_TIMEOUT = 30000; // 30ms timeout

// ===== Variables =====
float minDistance = 999.0;
float maxDistance = 0.0;
unsigned long lastUpdate = 0;

float readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ULTRASONIC_TIMEOUT);
  if (duration == 0) return 999.0;
  
  float distance = (duration * 0.034) / 2;
  return distance;
}

void setup() {
  Serial.begin(9600);
  Serial.println("=== ULTRASONIC DISTANCE DEBUG ===");
  Serial.println("Place objects at the detection point to find ideal range");
  Serial.println();
  
  Wire.begin(SDA_PIN, SCL_PIN);
  int s = lcd.begin(16, 2);
  if (s) {
    Serial.println("LCD initialization failed");
    while(1){}
  }
  lcd.backlight();
  lcd.clear();
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  lcd.setCursor(0, 0);
  lcd.print("Distance Debug");
  lcd.setCursor(0, 1);
  lcd.print("Place object...");
  delay(2000);
}

void loop() {
  float distance = readUltrasonicDistance();
  
  // Track min/max when object is present (less than 50cm)
  if (distance < 50.0) {
    if (distance < minDistance) minDistance = distance;
    if (distance > maxDistance) maxDistance = distance;
  }
  
  // Update LCD every 200ms
  if (millis() - lastUpdate > 200) {
    lastUpdate = millis();
    
    // Line 1: Current distance
    lcd.setCursor(0, 0);
    lcd.print("                ");
    lcd.setCursor(0, 0);
    lcd.print("Dist: ");
    if (distance > 100) {
      lcd.print("---");
    } else {
      lcd.print(distance, 1);
      lcd.print(" cm");
    }
    
    // Line 2: Min/Max range
    lcd.setCursor(0, 1);
    lcd.print("                ");
    lcd.setCursor(0, 1);
    lcd.print("R:");
    lcd.print(minDistance, 1);
    lcd.print("-");
    lcd.print(maxDistance, 1);
    lcd.print("cm");
    
    // Serial output
    Serial.print("Distance: ");
    if (distance > 100) {
      Serial.print("No object");
    } else {
      Serial.print(distance, 1);
      Serial.print(" cm");
    }
    Serial.print(" | Range seen: ");
    Serial.print(minDistance, 1);
    Serial.print(" - ");
    Serial.print(maxDistance, 1);
    Serial.println(" cm");
  }
  
  yield();
}
