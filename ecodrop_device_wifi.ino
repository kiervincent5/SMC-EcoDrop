#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <Servo.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// ===== CONFIG: Wi-Fi and API (edit these) =====
const char* WIFI_SSID = "Dc";
const char* WIFI_PASS = "12345678";
const char* API_HOST  = "192.168.227.225";   // PC LAN IP or domain
const uint16_t API_PORT = 8000;           // Back to original port
const char* API_KEY  = "41c7fc4c-a9e5-46de-946d-f1db2526a9a7"; // same as Device.api_key in Django
const char* API_DEVICE_HEARTBEAT_PATH = "/api/device/heartbeat/";
const char* API_DEVICE_DETECT_PATH    = "/api/device/detection/";
const char* API_USER_VERIFY_PATH      = "/api/user/verify/";    // added: user verify endpoint
const char* DEVICE_ID = "MOD01";           // same as Device.device_id in Django

// ===== PINS (NodeMCU ESP8266) =====
const uint8_t SDA_PIN   = D2;   // I2C SDA
const uint8_t SCL_PIN   = D1;   // I2C SCL
const int     TRIG_PIN  = D3;   // Ultrasonic trigger pin
const int     ECHO_PIN  = D4;   // Ultrasonic echo pin
const int     CAP_PIN   = D6;   // Capacitive sensor, HIGH near material (non-plastic on your PNP interface)
const int     SERVO_PIN = D7;   // Servo signal
const int     BUZZER_PIN= D0;   // Active buzzer (+) to D0, (−) to GND

// ===== LCD =====
hd44780_I2Cexp lcd;

// ===== SERVO =====
Servo gate;
const int RIGHT_POS  = 20;      // plastic -> right (ACCEPT)
const int LEFT_POS   = 160;     // not plastic -> left (REJECT)
const int CENTER_POS = 90;
const unsigned long ACTION_HOLD_MS = 1200;
unsigned long servoHoldUntil = 0;
int servoTarget = CENTER_POS;

// ===== DEBOUNCE / TIMING =====
const unsigned long CAP_CONFIRM_MS   = 40;
const unsigned long ULTRASONIC_CONFIRM_MS = 50;
const unsigned long RELATCH_MS       = 800;

// ===== ULTRASONIC SETTINGS =====
const float DETECTION_DISTANCE_CM = 4.0;  // Increased range: detects objects up to 30cm away
const unsigned long ULTRASONIC_TIMEOUT = 10000;  // 30ms timeout for ultrasonic reading

// Simplified detection timing
const unsigned long DETECTION_DELAY_MS = 1500;  // Wait 1.5s for sensors to stabilize before verifying
const unsigned long COOLDOWN_AFTER_PROCESS_MS = 2000;  // 2s cooldown after processing to prevent re-detection

// Bottle session timeout after verify
const unsigned long VERIFIED_IDLE_TIMEOUT_MS = 40000; // 40 seconds

// Buzzer durations
const unsigned long BEEP_SHORT_MS  = 120;   // accept
const unsigned long BEEP_REJECT_MS = 3000;  // reject

// ===== WIFI & API =====
WiFiClient wifiClient;
HTTPClient http;
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 seconds
unsigned long lastHeartbeat = 0;
bool wifiConnected = false;

// ===== USER / SESSION STATE =====
bool userVerified = false;
String currentUser = "";
String currentUserName = "";  // Store user's display name
unsigned long verifiedDeadline = 0;

// ===== MACHINE STATE =====
bool latched = false;

int  capStable = LOW,  capLast = LOW;
unsigned long capChangedAt = 0;

bool ultrasonicStable = false, ultrasonicLast = false;
unsigned long ultrasonicChangedAt = 0;
float lastDistance = 999.0;

bool detectionActive = false;
unsigned long detectionStart = 0;

unsigned long lastProcessedAt = 0;  // Track when last bottle was processed
unsigned long lastLcdAt = 0;

// ===== LCD helpers =====
void lcdTop(const String& s){
  lcd.setCursor(0,0); lcd.print("                ");
  lcd.setCursor(0,0); lcd.print(s.substring(0,16));
}
void lcdBottom(const String& s){
  lcd.setCursor(0,1); lcd.print("                ");
  lcd.setCursor(0,1); lcd.print(s.substring(0,16));
}

void showScanPrompt(){
  lcdTop("Please Scan your");
  lcdBottom("ID");
}
void showInsertPrompt(){
  lcdTop("Please insert");
  lcdBottom("plastic bottle");
}

// ===== Buzzer helpers =====
void buzzerOn()  { digitalWrite(BUZZER_PIN, HIGH); }
void buzzerOff() { digitalWrite(BUZZER_PIN, LOW);  }
void beepAccept(){ buzzerOn(); delay(BEEP_SHORT_MS); buzzerOff(); }
void buzzReject(){ buzzerOn(); delay(BEEP_REJECT_MS); buzzerOff(); }

// ===== Servo helpers =====
void servoActuate(int pos, unsigned long hold_ms){
  servoTarget = pos;
  servoHoldUntil = millis() + hold_ms;
  gate.write(servoTarget);
}
void serviceServo(){
  if (millis() <= servoHoldUntil){
    gate.write(servoTarget);
    digitalWrite(LED_BUILTIN, LOW);   // ESP8266 LED active LOW
  } else {
    gate.write(CENTER_POS);
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

// ===== WiFi Functions =====
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  lcdTop("Connecting WiFi");
  lcdBottom("Please wait...");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
    lcdBottom(String("Attempt ") + String(attempts));
  }
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    lcdTop("WiFi Connected");
    lcdBottom(WiFi.localIP().toString());
    delay(1200);
  } else {
    wifiConnected = false;
    lcdTop("WiFi Failed");
    lcdBottom("Check settings");
    delay(1200);
  }
}

int httpGET(const String& url, const char* apiKey, String& respOut) {
  WiFiClient net;
  HTTPClient http;
  
  Serial.print("HTTP: Attempting connection to: "); Serial.println(url);
  
  if (!http.begin(net, url)) {
    Serial.println("HTTP: Failed to begin connection");
    return -1;
  }
  
  http.setTimeout(10000);  // 10 second timeout
  http.addHeader("User-Agent", "EcoDrop-Arduino/1.0");
  if (apiKey && apiKey[0]) {
    http.addHeader("Authorization", String("Bearer ") + apiKey);
    Serial.println("HTTP: Added Authorization header");
  }
  
  Serial.println("HTTP: Sending GET request...");
  int code = http.GET();
  
  if (code > 0) {
    respOut = http.getString();
    Serial.print("HTTP: Success, response length: "); Serial.println(respOut.length());
  } else {
    Serial.print("HTTP: Error code: "); Serial.println(code);
    Serial.print("HTTP: Error string: "); Serial.println(http.errorToString(code));
  }
  
  http.end();
  return code;
}

int httpPOSTjson(const String& url, const char* apiKey, const String& jsonBody, String& respOut) {
  WiFiClient net;
  HTTPClient http;
  if (!http.begin(net, url)) return -1;
  http.addHeader("Content-Type", "application/json");
  if (apiKey && apiKey[0]) http.addHeader("Authorization", String("Bearer ") + apiKey);
  int code = http.POST(jsonBody);
  respOut = http.getString();
  http.end();
  return code;
}

// Verify user via API
bool apiVerifyUser(const String& code) {
  if (!wifiConnected || WiFi.status() != WL_CONNECTED) {
    Serial.println("ERROR: WiFi not connected");
    return false;
  }
  
  // Clean the code - handle student ID format like "C22-0369"
  String cleanCode = "";
  Serial.print("DEBUG: Processing characters: ");
  for (int i = 0; i < code.length(); i++) {
    char c = code.charAt(i);
    Serial.print("'"); Serial.print(c); Serial.print("'("); Serial.print((int)c); Serial.print(") ");
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-') {
      char upperC = (c >= 'a' && c <= 'z') ? (c - 'a' + 'A') : c;  // Manual uppercase conversion
      cleanCode += upperC;
    }
  }
  Serial.println();
  
  Serial.print("VERIFY: Cleaned student ID: '"); Serial.print(cleanCode); Serial.println("'");
  
  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_USER_VERIFY_PATH + "?code=" + cleanCode;
  Serial.print("VERIFY: URL: "); Serial.println(url);
  
  // Test basic connectivity
  WiFiClient testClient;
  Serial.print("NETWORK: Testing connection to "); Serial.print(API_HOST); Serial.print(":"); Serial.println(API_PORT);
  if (testClient.connect(API_HOST, API_PORT)) {
    Serial.println("NETWORK: Basic TCP connection successful");
    testClient.stop();
  } else {
    Serial.println("NETWORK: Basic TCP connection failed - server unreachable");
  }
  
  String resp;
  int httpCode = httpGET(url, API_KEY, resp);
  Serial.print("VERIFY: HTTP "); Serial.print(httpCode); Serial.print(" -> "); Serial.println(resp);
  
  if (httpCode != 200) {
    Serial.print("ERROR: HTTP request failed with code: "); Serial.println(httpCode);
    return false;
  }
  
  StaticJsonDocument<256> doc; // Increased size for debug info
  DeserializationError error = deserializeJson(doc, resp);
  if (error) {
    Serial.print("ERROR: JSON parsing failed: "); Serial.println(error.c_str());
    return false;
  }
  
  bool success = (bool)(doc["ok"] | false);
  if (!success) {
    Serial.print("ERROR: User verification failed. Message: ");
    Serial.println(doc["message"] | "Unknown error");
    
    // Print debug info if available
    if (doc["debug"]) {
      Serial.println("DEBUG INFO from server:");
      Serial.print("  Received student ID: "); Serial.println(doc["debug"]["received_student_id"] | "N/A");
      Serial.println("  Available student IDs in database:");
      JsonArray available = doc["debug"]["available_student_ids"];
      for (JsonVariant id : available) {
        Serial.print("    - "); Serial.println(id.as<String>());
      }
    }
  } else {
    Serial.println("SUCCESS: User verified!");
    
    // Extract user name from response for display
    if (doc["user"] && doc["user"]["full_name"]) {
      currentUserName = doc["user"]["full_name"].as<String>();
    } else if (doc["user"] && doc["user"]["username"]) {
      currentUserName = doc["user"]["username"].as<String>();
    } else {
      currentUserName = "User";
    }
  }
  
  return success;
}

// Heartbeat
void sendHeartbeat() {
  if (!wifiConnected || WiFi.status() != WL_CONNECTED) return;

  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_DEVICE_HEARTBEAT_PATH;

  DynamicJsonDocument doc(256);
  doc["status"] = "online";
  doc["device_id"] = DEVICE_ID;
  doc["sensor_data"]["cap"] = (capStable==HIGH ? 1:0);
  doc["sensor_data"]["ultrasonic"] = (ultrasonicStable ? 1:0);
  doc["sensor_data"]["distance_cm"] = lastDistance;

  String payload; serializeJson(doc, payload);
  String resp;
  (void)httpPOSTjson(url, API_KEY, payload, resp);
}

// Log detection
void sendBottleDetection(const String& sortResult, unsigned long widthMs, const String& userCode) {
  if (!wifiConnected || WiFi.status() != WL_CONNECTED) return;

  String url = String("http://") + API_HOST + ":" + String(API_PORT) + API_DEVICE_DETECT_PATH;

  DynamicJsonDocument doc(1024);
  doc["device_id"]   = DEVICE_ID;
  doc["sort_result"] = sortResult;
  if (userCode.length() > 0) doc["user_id"] = userCode;
  doc["sensor_data"]["width_ms"]   = widthMs;
  doc["sensor_data"]["cap_stable"] = capStable;
  doc["sensor_data"]["ultrasonic_stable"] = ultrasonicStable;
  doc["sensor_data"]["distance_cm"] = lastDistance;

  String payload; serializeJson(doc, payload);
  String resp;
  int httpCode = httpPOSTjson(url, API_KEY, payload, resp);
  Serial.print("POST "); Serial.print(httpCode); Serial.print(" -> "); Serial.println(resp);
}

// ===== Non-blocking scanner read (poll) =====
String pollScannerOnce() {
  static String buf = "";
  while (Serial.available()) {
    char c = (char)Serial.read();
    // Handle different line endings: \r, \n, or \r\n
    if (c == '\r' || c == '\n') {
      if (buf.length() > 0) {
        String out = buf; 
        out.trim(); // Remove any whitespace
        buf = "";
        Serial.print("SCANNED RAW: '"); Serial.print(out); Serial.println("'");
        return out;
      }
    } else if (c >= 32 && c <= 126) { // Only printable ASCII characters
      if (buf.length() < 48) buf += c;
    }
  }
  return "";
}

// ===== Decision logic based on sensor combination =====
void processBottleDetection(){
  // Check sensor states after detection delay
  bool ultrasonicDetected = ultrasonicStable;
  bool capacitiveDetected = (capStable == HIGH);
  
  String sortResult;
  bool isAccepted = false;
  
  if (ultrasonicDetected && capacitiveDetected) {
    // Both sensors detected - REJECT (NO SERVO MOVEMENT)
    sortResult = "invalid";
    isAccepted = false;
    
    lcdTop("Not plastic!");
    lcdBottom("Try again");
    delay(1500);  // Show error message longer
    buzzReject(); // 3 second buzz
    // Servo stays in CENTER - no movement for rejected items
    
  } else if (ultrasonicDetected && !capacitiveDetected) {
    // Only ultrasonic detected - ACCEPT
    sortResult = "plastic";
    isAccepted = true;
    
    lcdTop("Plastic bottle");
    lcdBottom("detected!");
    beepAccept(); // Single beep
    servoActuate(RIGHT_POS, ACTION_HOLD_MS);
    delay(2000);  // Show detection longer
    
    lcdTop("Adding points");
    lcdBottom("to " + currentUserName.substring(0,12));
    delay(2500);  // Show points message longer
    
  } else {
    // No valid detection - ignore
    showInsertPrompt();
    verifiedDeadline = millis() + VERIFIED_IDLE_TIMEOUT_MS;
    detectionActive = false;
    return;
  }
  
  // Log the detection
  sendBottleDetection(sortResult, 0, currentUser);
  
  // Return to insert prompt (timer keeps running)
  showInsertPrompt();
  
  // Reset detection state with cooldown to prevent immediate re-detection
  detectionActive = false;
  lastProcessedAt = millis();  // Mark processing time for cooldown
}

// ===== Inputs =====
// ===== Ultrasonic sensor reading =====
float readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ULTRASONIC_TIMEOUT);
  if (duration == 0) return 999.0; // timeout or no echo
  
  float distance = (duration * 0.034) / 2; // Convert to cm
  return distance;
}

void debounceInputs(){
  if (!userVerified) return; // do not detect until a user is verified

  unsigned long now = millis();

  // ULTRASONIC
  float distance = readUltrasonicDistance();
  lastDistance = distance;
  bool ultrasonicRead = (distance <= DETECTION_DISTANCE_CM && distance > 0);
  
  if (ultrasonicRead != ultrasonicLast){ 
    ultrasonicLast = ultrasonicRead; 
    ultrasonicChangedAt = now; 
  }
  if (ultrasonicRead != ultrasonicStable && (now - ultrasonicChangedAt) >= ULTRASONIC_CONFIRM_MS){
    ultrasonicStable = ultrasonicRead;
  }

  // CAP
  int capRead = digitalRead(CAP_PIN);
  if (capRead != capLast){ capLast = capRead; capChangedAt = now; }
  if (capRead != capStable && (now - capChangedAt) >= CAP_CONFIRM_MS){
    capStable = capRead;
  }
}

// ===== Detection handling =====
void handleDetection(){
  if (!userVerified) return; // ignore detection until verified

  unsigned long now = millis();

  // Start detection when any sensor triggers (with cooldown check)
  if (!detectionActive){
    // Check if cooldown period has passed since last processing
    bool cooldownPassed = (now - lastProcessedAt) >= COOLDOWN_AFTER_PROCESS_MS;
    
    if (cooldownPassed && (ultrasonicStable || capStable == HIGH)){
      detectionActive = true;
      detectionStart = now;
      // Reset timer on bottle insertion attempt
      verifiedDeadline = millis() + VERIFIED_IDLE_TIMEOUT_MS;
    }
  }

  // Process detection after delay
  if (detectionActive && (now - detectionStart) >= DETECTION_DELAY_MS){
    processBottleDetection();
  }

  // Check timeout back to Scan ID after 40 seconds of no activity
  if (userVerified && millis() > verifiedDeadline) {
    userVerified = false;
    currentUser = "";
    currentUserName = "";  // Clear user name
    lcdTop("Session expired");
    lcdBottom("Scan ID again");
    delay(1500);
    showScanPrompt();
  }
}

// ===== Setup =====
void setup(){
  // Scanner on RX0 (GPIO3)
  Serial.begin(9600);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Wire.begin(SDA_PIN, SCL_PIN);
  int s = lcd.begin(16,2);
  if (s){
    Serial.println("LCD initialization failed");
    while(1){}
  }
  lcd.backlight();
  lcd.clear();

  pinMode(CAP_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  buzzerOff();

  gate.attach(SERVO_PIN, 500, 2500);
  gate.write(CENTER_POS);

  connectWiFi();

  showScanPrompt();

  Serial.println("EcoDrop Device Started");
  Serial.println("WiFi Status: " + String(wifiConnected ? "Connected" : "Disconnected"));
}

// ===== Loop =====
void loop(){
  // 1) Always check for new ID scan (even if user already verified)
  String scanned = pollScannerOnce();
  if (scanned.length() > 0) {
    // New ID scanned - immediately switch to this user
    lcdTop("Verifying...");
    lcdBottom(scanned.substring(0,16));
    bool ok = apiVerifyUser(scanned);
    if (ok) {
      userVerified = true;
      currentUser = scanned;
      lcdTop("User verified");
      lcdBottom("Welcome!");
      delay(2000);  // Longer delay to read
      
      // Show user name
      lcdTop("Hello");
      lcdBottom(currentUserName.substring(0,16));
      delay(2500);  // Show name for 2.5 seconds
      
      showInsertPrompt();
      verifiedDeadline = millis() + VERIFIED_IDLE_TIMEOUT_MS;
      
      // Reset detection state for new user
      detectionActive = false;
      lastProcessedAt = 0;
    } else {
      lcdTop("ID not found");
      lcdBottom("Scan again");
      delay(1000);
      if (!userVerified) showScanPrompt();  // Only show scan prompt if no user active
    }
  }

  // 2) Normal processing when verified
  if (userVerified) {
    debounceInputs();
    handleDetection();
  }

  unsigned long now = millis();

  // Heartbeat
  if (wifiConnected && (now - lastHeartbeat) > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = now;
  }

  // Wi-Fi reconnect
  if (WiFi.status() != WL_CONNECTED && wifiConnected) {
    wifiConnected = false;
    lcdTop("WiFi Lost");
    lcdBottom("Reconnecting...");
    connectWiFi();
    if (userVerified) showInsertPrompt(); else showScanPrompt();
  }

  // Keep showing insert prompt (no technical sensor data)
  if (userVerified && now - lastLcdAt > 2000){
    lastLcdAt = now;
    showInsertPrompt();  // Just refresh the insert prompt
  }

  serviceServo();
  yield();
}
