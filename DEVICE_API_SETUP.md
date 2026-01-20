# 🤖 EcoDrop Device API Setup Guide

Complete guide to connect your EcoDrop hardware device to your web application on Render.

---

## 📋 Overview

Your EcoDrop device (ESP8266 NodeMCU) communicates with your Django web app through API endpoints. This guide covers:
- Configuring Arduino code for production (HTTPS)
- Setting up Django to accept device requests
- Testing the connection

---

## 🔧 Step 1: Get Your Render URL

1. Go to your Render dashboard: **https://dashboard.render.com**
2. Click on your **ecodrop-web** service
3. Find your URL at the top (e.g., `ecodrop-web.onrender.com`)
4. **Copy this URL** - you'll need it!

---

## 🎛️ Step 2: Update Arduino Code

### **File:** `ecodrop_device_wifi_improved.ino`

Find these lines (around line 15):

```cpp
// PRODUCTION: Use your Render app URL (CHANGE THIS to your actual Render URL)
const char* API_HOST  = "ecodrop-web.onrender.com";  // YOUR Render URL here
const uint16_t API_PORT = 443;           // HTTPS port for production
const bool USE_HTTPS = true;             // Set to true for production
```

**Replace `ecodrop-web.onrender.com` with YOUR actual Render URL!**

### **Important:** 
- ❌ Do NOT include `https://` in the URL
- ✅ Just the domain: `your-app.onrender.com`
- ✅ Port should be `443` for HTTPS
- ✅ `USE_HTTPS` should be `true`

---

## 🌐 Step 3: Update Django Settings

### **File:** `ecodrop_project/settings.py`

**Already updated!** But verify these lines:

```python
ALLOWED_HOSTS = [
    # ... other hosts ...
    'YOUR-RENDER-URL.onrender.com',  # CHANGE THIS
]

CSRF_TRUSTED_ORIGINS = [
    'https://YOUR-RENDER-URL.onrender.com',  # CHANGE THIS
    # ... other origins ...
]
```

**Replace `YOUR-RENDER-URL` with your actual Render subdomain!**

---

## 📡 Step 4: Create Device in Admin Panel

Before your hardware can connect, you need to create it in the database:

1. **Go to:** `https://your-app.onrender.com/admin`
2. **Login** with admin credentials
3. **Click:** "Devices" under CORE section
4. **Click:** "Add Device"
5. **Fill in:**
   - **Device ID:** `MOD01` (must match Arduino code)
   - **Device name:** `EcoDrop Station 1`
   - **Location:** `Main Building - Ground Floor`
6. **Save** - The system will auto-generate an API key
7. **Copy the API key** from the device details

---

## 🔑 Step 5: Update API Key in Arduino

In your Arduino code (`ecodrop_device_wifi_improved.ino`), update:

```cpp
const char* API_KEY = "YOUR-API-KEY-FROM-DJANGO-ADMIN";
```

Replace with the actual API key from Step 4!

---

## 📤 Step 6: Upload Code to ESP8266

1. **Open** `ecodrop_device_wifi_improved.ino` in Arduino IDE
2. **Select** your board: Tools → Board → NodeMCU 1.0 (ESP-12E Module)
3. **Select** your port: Tools → Port → (your COM port)
4. **Click** Upload button
5. **Wait** for upload to complete
6. **Open** Serial Monitor (115200 baud rate)

---

## 🧪 Step 7: Test the Connection

### **Monitor Serial Output:**

You should see:
```
WiFi connected
IP: 192.168.x.x
HTTP: Attempting connection to: https://your-app.onrender.com/api/device/heartbeat/
HTTPS: Connection successful
HTTP: Success, response length: XX
```

### **Check Admin Panel:**

1. Go to admin panel → Devices
2. Your device should show:
   - **Status:** Online (green)
   - **Last heartbeat:** Recent timestamp
3. Click "View Logs" to see device activity

---

## 🔍 API Endpoints Used by Device

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/device/heartbeat/` | POST | Device sends heartbeat every 30 seconds |
| `/api/device/detection/` | POST | Reports bottle detection & sorting |
| `/api/user/verify/` | POST | Verifies student/faculty ID for points |

All endpoints require:
- **Authorization:** `Bearer YOUR-API-KEY`
- **Content-Type:** `application/json`

---

## 🐛 Troubleshooting

### **Device Can't Connect to WiFi**

**Check:**
- WiFi credentials in Arduino code are correct
- WiFi network is 2.4GHz (ESP8266 doesn't support 5GHz)
- Router allows device connections

**Serial Monitor shows:**
```
WiFi connecting...
WiFi Failed
```

**Fix:** Update `WIFI_SSID` and `WIFI_PASS` in Arduino code

---

### **WiFi Connected but API Fails**

**Serial Monitor shows:**
```
WiFi connected
HTTP: Error code: -1
HTTPS: Failed to begin connection
```

**Possible causes:**
1. **Incorrect Render URL** - Check `API_HOST` matches your Render URL
2. **Wrong port** - Should be `443` for HTTPS
3. **Certificate issues** - Code uses `setInsecure()` which should work

**Fix:**
- Verify `API_HOST` = your Render URL (without https://)
- Verify `API_PORT` = `443`
- Verify `USE_HTTPS` = `true`

---

### **HTTP 401 Unauthorized**

**Serial Monitor shows:**
```
HTTP: Error code: 401
```

**Cause:** Invalid or missing API key

**Fix:**
1. Go to Django admin → Devices
2. Copy the API key for your device
3. Update `API_KEY` in Arduino code
4. Re-upload code to ESP8266

---

### **HTTP 403 Forbidden**

**Serial Monitor shows:**
```
HTTP: Error code: 403
```

**Cause:** CORS or CSRF protection blocking request

**Fix:**
- Settings already updated with CORS support
- Make sure you pushed latest code to GitHub
- Wait for Render to redeploy
- Device API endpoints are exempt from CSRF

---

### **HTTP 404 Not Found**

**Serial Monitor shows:**
```
HTTP: Error code: 404
```

**Cause:** API endpoint doesn't exist

**Fix:**
- Check `API_DEVICE_HEARTBEAT_PATH` = `/api/device/heartbeat/`
- Verify Django URLs are configured
- Check Render deployment logs for errors

---

### **Device Shows Offline in Admin**

**Possible causes:**
1. Device not sending heartbeats
2. Wrong device ID
3. API key mismatch

**Fix:**
1. Check Serial Monitor for errors
2. Verify `DEVICE_ID` in Arduino matches database
3. Verify `API_KEY` matches database
4. Device should send heartbeat every 30 seconds

---

## 🔄 Switching Between Local & Production

### **For Local Testing (PC):**

In Arduino code, comment out production and uncomment local:

```cpp
// PRODUCTION: (Comment these out)
// const char* API_HOST  = "ecodrop-web.onrender.com";
// const uint16_t API_PORT = 443;
// const bool USE_HTTPS = true;

// LOCAL TESTING: (Uncomment these)
const char* API_HOST  = "192.168.1.XXX";   // Your PC IP
const uint16_t API_PORT = 8000;            // Django dev server port
const bool USE_HTTPS = false;              // HTTP for local
```

Run Django locally:
```bash
python manage.py runserver 0.0.0.0:8000
```

### **For Production (Render):**

Uncomment production settings, comment out local.

---

## 📊 How It Works

```
┌─────────────────┐
│  ESP8266 Device │
│   (EcoDrop)     │
└────────┬────────┘
         │
         │ HTTPS (Port 443)
         │ Bearer Token Auth
         │
         ▼
┌─────────────────┐
│  Render Server  │
│   Django App    │
└────────┬────────┘
         │
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │
│   (User data,   │
│   transactions) │
└─────────────────┘
```

**Flow:**
1. Device connects to WiFi
2. Device sends HTTPS POST to `/api/device/heartbeat/`
3. Django validates API key
4. Django updates device status in database
5. Device continues operating

---

## ✅ Success Checklist

- [ ] Render URL copied
- [ ] Arduino code updated with Render URL
- [ ] `USE_HTTPS = true` in Arduino
- [ ] `API_PORT = 443` in Arduino
- [ ] Device created in Django admin
- [ ] API key copied from admin
- [ ] API key updated in Arduino code
- [ ] Code uploaded to ESP8266
- [ ] WiFi connected (check Serial Monitor)
- [ ] Heartbeat successful (check Serial Monitor)
- [ ] Device shows "Online" in admin panel
- [ ] Django settings updated on GitHub
- [ ] Render redeployed with new settings

---

## 🔐 Security Notes

### **Current Setup (Testing):**
- Uses `setInsecure()` - skips SSL certificate validation
- Good for testing, acceptable for closed network

### **For Enhanced Security (Future):**

Add SSL certificate verification:

```cpp
// In Arduino code
WiFiClientSecure secureClient;

// Option 1: Use certificate fingerprint
const char* fingerprint = "AA:BB:CC:...";
secureClient.setFingerprint(fingerprint);

// Option 2: Use CA certificate
const char* ca_cert = "-----BEGIN CERTIFICATE-----\n...";
secureClient.setCACert(ca_cert);
```

Get certificate:
```bash
openssl s_client -connect ecodrop-web.onrender.com:443 < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout
```

---

## 📞 Support

### **Check These First:**
1. Serial Monitor output (115200 baud)
2. Render deployment logs
3. Django admin → Devices → View Logs
4. Network connectivity

### **Common Issues:**
- **No WiFi:** Check credentials, 2.4GHz network
- **401 Error:** Wrong API key
- **403 Error:** CORS/CSRF (settings.py)
- **404 Error:** Wrong endpoint URL
- **Connection timeout:** Wrong host/port

---

## 📚 Related Files

- `ecodrop_device_wifi_improved.ino` - Arduino device code
- `ecodrop_project/settings.py` - Django configuration
- `core/views.py` - API endpoint handlers
- `core/models.py` - Device database model

---

**Last Updated:** October 2025  
**Platform:** Render.com  
**Device:** ESP8266 NodeMCU  
**Protocol:** HTTPS with Bearer Token Auth
