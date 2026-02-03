// ===== SERVO MOTOR TEST =====
// Upload this to test if your servo is working properly
// Expected behavior: Servo moves LEFT -> CENTER -> RIGHT -> CENTER repeatedly

#include <Servo.h>

const int SERVO_PIN = D7;  // Same pin as your EcoDrop device

Servo testServo;

const int LEFT_POS   = 160;  // Left position (reject)
const int CENTER_POS = 90;   // Center position
const int RIGHT_POS  = 20;   // Right position (accept/plastic)

void setup() {
  Serial.begin(9600);
  Serial.println("\n=== SERVO MOTOR TEST ===");
  Serial.println("Pin: D7");
  Serial.println("Positions: LEFT=160, CENTER=90, RIGHT=20\n");
  
  testServo.attach(SERVO_PIN, 500, 2500);
  testServo.write(CENTER_POS);
  delay(1000);
  
  Serial.println("Starting test sequence...\n");
}

void loop() {
  // Move to LEFT (160 degrees)
  Serial.println(">> Moving to LEFT (160 degrees)");
  testServo.write(LEFT_POS);
  delay(2000);
  
  // Move to CENTER (90 degrees)
  Serial.println(">> Moving to CENTER (90 degrees)");
  testServo.write(CENTER_POS);
  delay(2000);
  
  // Move to RIGHT (20 degrees)
  Serial.println(">> Moving to RIGHT (20 degrees)");
  testServo.write(RIGHT_POS);
  delay(2000);
  
  // Back to CENTER
  Serial.println(">> Moving to CENTER (90 degrees)");
  testServo.write(CENTER_POS);
  delay(2000);
  
  Serial.println("\n--- Cycle complete, repeating... ---\n");
}
