# ⚡ Quick Start: Deploy to Render in 10 Minutes

## 🎯 Overview

Deploy your EcoDrop Django app to **Render.com** for FREE!

---

## Step 1: Sign Up on Render

1. Go to: **https://render.com/register**
2. Click **"Sign up with GitHub"**
3. Authorize Render

---

## Step 2: Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Settings:
   - **Name:** `ecodrop-db`
   - **Database:** `ecodrop`
   - **Region:** Choose closest to you
   - **Plan:** **Free**
3. Click **"Create Database"**
4. Wait ~2 minutes for it to become "Available"

---

## Step 3: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Click **"Build and deploy from a Git repository"**
3. Connect GitHub and select **`SMC_EcoDrop`**
4. Click **"Connect"**

---

## Step 4: Configure Service

### Basic Info
- **Name:** `ecodrop-web`
- **Region:** Same as database
- **Branch:** `main`
- **Runtime:** `Python 3`

### Build & Start
- **Build Command:** `chmod +x build.sh && ./build.sh`
- **Start Command:** `gunicorn ecodrop_project.wsgi:application`

### Plan
- **Instance Type:** **Free**

---

## Step 5: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** for each:

```
PYTHON_VERSION          3.11.0
DEBUG                   False
DJANGO_SECRET_KEY       8laq0x(#(v-tkywyj87ka2b_n8tczc04u(v1hp+^7vie54v!8^
DJANGO_SUPERUSER_USERNAME    admin
DJANGO_SUPERUSER_EMAIL       admin@ecodrop.com
DJANGO_SUPERUSER_PASSWORD    YourSecurePassword123!
```

### Add Database Connection

1. Click **"Add Environment Variable"**
2. **Key:** `DATABASE_URL`
3. **Value:** Click **"Add from Database"**
4. Select: **`ecodrop-db`**
5. Property: **Internal Database URL**

---

## Step 6: Deploy!

1. Click **"Create Web Service"**
2. Wait ~3-5 minutes for build
3. Watch logs for "Live" status

---

## Step 7: Access Your App

Once "Live":

- **Main App:** `https://ecodrop-web.onrender.com/`
- **Admin:** `https://ecodrop-web.onrender.com/admin`

**Login:**
- Username: `admin`
- Password: (your `DJANGO_SUPERUSER_PASSWORD`)

---

## Step 8: Update Settings (Optional)

After deployment, update `settings.py`:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://ecodrop-web.onrender.com',  # Your Render URL
    # ...existing entries...
]
```

Push to GitHub - Render will auto-redeploy!

---

## ✅ Done!

Your EcoDrop app is now live and accessible!

**See `RENDER_DEPLOYMENT.md` for detailed guide**

---

## ⚠️ Free Tier Note

Free tier apps sleep after 15 min of inactivity. First request after sleeping takes ~30 seconds to wake up.

---

## 📞 Need Help?

Check:
- Build logs in Render dashboard
- `RENDER_DEPLOYMENT.md` for troubleshooting
- Render docs: https://render.com/docs
