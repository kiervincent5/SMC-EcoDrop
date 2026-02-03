#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <Servo.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>

// ===== CONFIG: Wi-Fi and API =====
const char* WIFI_SSID = "Vince";
const char* WIFI_PASS = "vinceba1";

// LOCAL TESTING
const char* API_HOST  = "10.248.177.225";
const uint16_t API_PORT = 8000;
const bool USE_HTTPS = false;

const char* API_KEY  = "a4595382-edde-4a05-aa01-171afacc97c8";
const char* API_DEVICE_HEARTBEAT_PATH = "/api/device/heartbeat/";
const char* API_DEVICE_DETECT_PATH    = "/api/device/detection/";
const char* API_USER_VERIFY_PATH      = "/api/user/verify/";
const char* DEVICE_ID = "MOD01";

// ===== PINS (NodeMCU ESP8266) =====
const uint8_t SDA_PIN   = D2;
const uint8_t SCL_PIN   = D1;
const int     TRIG_PIN  = D3;
const int     ECHO_PIN  = D4;
const int     CAP_PIN   = D6;   // Capacitive sensor
const int     SERVO_PIN = D7;
const int     BUZZER_PIN= D0;
const uint8_t SCANNER_TRIGGER_PIN = D8;

// ===== LCD =====
hd44780_I2Cexp lcd;

// ===== SERVO =====
Servo gate;
const int RIGHT_POS  = 20;
const int LEFT_POS   = 160;
const int CENTER_POS = 90;
const unsigned long ACTION_HOLD_MS = 1200;
unsigned long servoHoldUntil = 0;
int servoTarget = CENTER_POS;

// ===== TIMING =====
const unsigned long CAP_CONFIRM_MS   = 40;
const unsigned long ULTRASONIC_CONFIRM_MS = 50;

const float   DETECTION_MIN_CM = 2.0;
const float   DETECTION_MAX_CM = 5.0;
const unsigned long ULTRASONIC_TIMEOUT = 10000;
const unsigned long DETECTION_DELAY_MS = 500;
const unsigned long COOLDOWN_AFTER_PROCESS_MS = 1000;
const unsigned long VERIFIED_IDLE_TIMEOUT_MS = 40000;

// Buzzer
const unsigned long BEEP_SHORT_MS  = 120;
const unsigned long BEEP_REJECT_MS = 3000;

// Scanner
const unsigned long SCANNER_TRIGGER_INTERVAL = 1000;
unsigned long lastScannerTrigger = 0;
unsigned long scannerTriggerEnd = 0;
bool scannerTriggerActive = false;

// ===== WIFI & API =====
WiFiClient wifiClient;
HTTPClient http;
const unsigned long HEARTBEAT_INTERVAL = 30000;
unsigned long lastHeartbeat = 0;
bool wifiConnected = false;

// ===== USER / SESSION =====
bool userVerified = false;
String currentUser = "";
String currentUserName = "";
unsigned long verifiedDeadline = 0;

// ===== SENSOR STATE =====
int capStable = LOW, capLast = LOW;
unsigned long capChangedAt = 0;

bool ultrasonicStable = false, ultrasonicLast = false;
unsigned long ultrasonicChangedAt = 0;
float lastDistance = 999.0;

bool detectionActive = false;
unsigned long detectionStart = 0;
unsigned long lastProcessedAt = 0;
unsigned long lastLcdAt = 0;

// ===== HELPERS =====
void triggerScanner() {
  if (!scannerTriggerActive) {
    digitalWrite(SCANNER_TRIGGER_PIN, LOW);
    scannerTriggerActive = true;
    scannerTriggerEnd = millis() + 300;
  }
}

void serviceScannerTrigger() {
  if (scannerTriggerActive && millis() >= scannerTriggerEnd) {
    digitalWrite(SCANNER_TRIGGER_PIN, HIGH);
    scannerTriggerActive = false;
  }
}

void lcdTop(const String& s){
  lcd.setCursor(0,0); lcd.print("                ");
  lcd.setCursor(0,0); lcd.print(s.substring(0,16));
}

void lcdBottom(const String& s){
  lcd.setCursor(0,1); lcd.print("                ");
  lcd.setCursor(0,1); lcd.print(s.substring(0,16));
}

void showScanPrompt(){ lcdTop("Please Scan your"); lcdBottom("ID"); }
void showInsertPrompt(){ lcdTop("Please insert"); lcdBottom("plastic bottle"); }

void buzzerOn()  { digitalWrite(BUZZER_PIN, HIGH); }
void buzzerOff() { digitalWrite(BUZZER_PIN, LOW);  }
void beepAccept(){ buzzerOn(); delay(BEEP_SHORT_MS); buzzerOff(); }
void buzzReject(){ buzzerOn(); delay(BEEP_REJECT_MS); buzzerOff(); }

void servoActuate(int pos, unsigned long hold_ms){
  servoTarget = pos;
  servoHoldUntil = millis() + hold_ms;
  gate.write(servoTarget);
}

void serviceServo(){
  if (millis() <= servoHoldUntil){
    gate.write(servoTarget);
    digitalWrite(LED_BUILTIN, LOW);
  } else {
    gate.write(CENTER_POS);
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

// ===== WiFi =====
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  lcdTop("Connecting WiFi");
  lcdBottom("Please wait...");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    lcdTop("WiFi Connected");
    lcdBottom(WiFi.localIP().toString());
    delay(1200);
  } else {
    wifiConnected = false;
    lcdTop("WiFi Failed");
    delay(1200);
  }
}

int httpGET(const String& url, const char* apiKey, String& respOut) {
  WiFiClient client;
  http.begin(client, url);
  http.setTimeout(10000);
  if (apiKey && apiKey[0]) http.addHeader("Authorization", String("Bearer ") + apiKey);
  int code = http.GET();
  if (code > 0) respOut = http.getString();
  http.end();
  return code;
}

int httpPOSTjson(const String& url, const char* apiKey, const String& jsonBody, String& respOut) {
  WiFiClient client;
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  if (apiKey && apiKey[0]) http.addHeader("Authorization", String("Bearer ") + apiKey);
  int code = http.POST(jsonBody);
  respOut = http.getString();
  http.end();
  return code;
}

bool apiVerifyUser(const String& code) {
  if (!wifiConnected) return false;
  
  String cleanCode = "";
  for (int i = 0; i < code.length(); i++) {
    char c = code.charAt(i);
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-') {
      cleanCode += (c >= 'a' && c <= 'z') ? (c - 'a' + 'A') : c;
    }
  }
  
  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_USER_VERIFY_PATH + "?code=" + cleanCode;
  String resp;
  int httpCode = httpGET(url, API_KEY, resp);
  
  if (httpCode != 200) return false;
  
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, resp)) return false;
  
  bool success = doc["ok"] | false;
  if (success) {
    if (doc["user"]["full_name"]) currentUserName = doc["user"]["full_name"].as<String>();
    else currentUserName = "User";
  }
  return success;
}

void sendHeartbeat() {
  if (!wifiConnected) return;
  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_DEVICE_HEARTBEAT_PATH;
  DynamicJsonDocument doc(256);
  doc["status"] = "online";
  doc["device_id"] = DEVICE_ID;
  String payload; serializeJson(doc, payload);
  String resp;
  httpPOSTjson(url, API_KEY, payload, resp);
}

void sendBottleDetection(const String& sortResult, const String& userCode) {
  if (!wifiConnected) return;
  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_DEVICE_DETECT_PATH;
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["sort_result"] = sortResult;
  if (userCode.length() > 0) doc["user_id"] = userCode;
  String payload; serializeJson(doc, payload);
  String resp;
  httpPOSTjson(url, API_KEY, payload, resp);
}

String pollScannerOnce() {
  static String buf = "";
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r' || c == '\n') {
      if (buf.length() > 0) {
        String out = buf;
        out.trim();
        buf = "";
        return out;
      }
    } else if (c >= 32 && c <= 126) {
      if (buf.length() < 48) buf += c;
    }
  }
  return "";
}

// ===== DETECTION LOGIC (ULTRASONIC + CAPACITIVE ONLY) =====
void processBottleDetection(){
  bool ultrasonicDetected = ultrasonicStable;
  bool capacitiveActive = (capStable == HIGH);  // HIGH = plastic detected
  
  String sortResult;
  
  // PLASTIC: Ultrasonic + Capacitive both active
  if (ultrasonicDetected && capacitiveActive) {
    sortResult = "plastic";
    lcdTop("Plastic bottle");
    lcdBottom("detected!");
    beepAccept();
    servoActuate(RIGHT_POS, ACTION_HOLD_MS);
    delay(2000);
    lcdTop("Adding points");
    lcdBottom("to " + currentUserName.substring(0,12));
    delay(2500);
  }
  // NOT PLASTIC: Ultrasonic active but Capacitive not
  else if (ultrasonicDetected && !capacitiveActive) {
    sortResult = "invalid";
    lcdTop("Not plastic!");
    lcdBottom("pls try again");
    delay(2000);
    buzzReject();
  }
  // NO VALID DETECTION
  else {
    showInsertPrompt();
    detectionActive = false;
    return;
  }
  
  sendBottleDetection(sortResult, currentUser);
  showInsertPrompt();
  detectionActive = false;
  lastProcessedAt = millis();
}

float readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ULTRASONIC_TIMEOUT);
  if (duration == 0) return 999.0;
  return (duration * 0.034) / 2;
}

void debounceInputs(){
  if (!userVerified) return;
  unsigned long now = millis();

  // ULTRASONIC
  float distance = readUltrasonicDistance();
  lastDistance = distance;
  bool ultrasonicRead = (distance >= DETECTION_MIN_CM && distance <= DETECTION_MAX_CM);
  
  if (ultrasonicRead != ultrasonicLast){ 
    ultrasonicLast = ultrasonicRead; 
    ultrasonicChangedAt = now; 
  }
  if (ultrasonicRead != ultrasonicStable && (now - ultrasonicChangedAt) >= ULTRASONIC_CONFIRM_MS){
    ultrasonicStable = ultrasonicRead;
  }

  // CAPACITIVE
  int capRead = digitalRead(CAP_PIN);
  if (capRead != capLast){ capLast = capRead; capChangedAt = now; }
  if (capRead != capStable && (now - capChangedAt) >= CAP_CONFIRM_MS){
    capStable = capRead;
  }
}

void handleDetection(){
  if (!userVerified) return;
  unsigned long now = millis();

  if (!detectionActive){
    bool cooldownPassed = (now - lastProcessedAt) >= COOLDOWN_AFTER_PROCESS_MS;
    if (cooldownPassed && ultrasonicStable){
      detectionActive = true;
      detectionStart = now;
      verifiedDeadline = millis() + VERIFIED_IDLE_TIMEOUT_MS;
    }
  }

  if (detectionActive && (now - detectionStart) >= DETECTION_DELAY_MS){
    processBottleDetection();
  }

  if (userVerified && millis() > verifiedDeadline) {
    userVerified = false;
    currentUser = "";
    currentUserName = "";
    lcdTop("Session expired");
    lcdBottom("Scan ID again");
    delay(1500);
    showScanPrompt();
  }
}

// ===== SETUP =====
void setup(){
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Wire.begin(SDA_PIN, SCL_PIN);
  lcd.begin(16,2);
  lcd.backlight();
  lcd.clear();

  pinMode(CAP_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  buzzerOff();
  
  pinMode(SCANNER_TRIGGER_PIN, OUTPUT);
  digitalWrite(SCANNER_TRIGGER_PIN, HIGH);

  gate.attach(SERVO_PIN, 500, 2500);
  gate.write(CENTER_POS);

  connectWiFi();
  showScanPrompt();
}

// ===== LOOP =====
void loop(){
  String scanned = pollScannerOnce();
  if (scanned.length() > 0) {
    lcdTop("Verifying...");
    lcdBottom(scanned.substring(0,16));
    if (apiVerifyUser(scanned)) {
      userVerified = true;
      currentUser = scanned;
      lcdTop("User verified");
      lcdBottom("Welcome!");
      delay(2000);
      lcdTop("Hello");
      lcdBottom(currentUserName.substring(0,16));
      delay(2500);
      showInsertPrompt();
      verifiedDeadline = millis() + VERIFIED_IDLE_TIMEOUT_MS;
      detectionActive = false;
      lastProcessedAt = 0;
    } else {
      lcdTop("ID not found");
      lcdBottom("Scan again");
      delay(1000);
      if (!userVerified) showScanPrompt();
    }
  }

  if (millis() - lastScannerTrigger > SCANNER_TRIGGER_INTERVAL) {
    triggerScanner();
    lastScannerTrigger = millis();
  }

  if (userVerified) {
    debounceInputs();
    handleDetection();
  }

  unsigned long now = millis();

  if (wifiConnected && (now - lastHeartbeat) > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = now;
  }

  if (WiFi.status() != WL_CONNECTED && wifiConnected) {
    wifiConnected = false;
    lcdTop("WiFi Lost");
    connectWiFi();
    if (userVerified) showInsertPrompt(); else showScanPrompt();
  }

  if (userVerified && now - lastLcdAt > 2000){
    lastLcdAt = now;
    showInsertPrompt();
  }

  serviceServo();
  serviceScannerTrigger();
  yield();
}
