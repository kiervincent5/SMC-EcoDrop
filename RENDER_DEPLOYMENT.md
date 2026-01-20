# 🎨 Render.com Deployment Guide for EcoDrop

Deploy your EcoDrop Django application to Render.com for **FREE** with automatic superuser creation!

---

## 🆓 Why Render?

- ✅ **Free tier** includes web services + PostgreSQL
- ✅ **512MB RAM** free tier
- ✅ Automatic deployments from GitHub
- ✅ Free SSL certificates
- ✅ Easy Django setup
- ✅ Similar to Railway but FREE

---

## 📋 Prerequisites

- GitHub account with your code pushed
- Render.com account (free)

---

## 🚀 Deployment Steps

### **Step 1: Create Render Account**

1. Go to **https://render.com/register**
2. Click **"Sign up with GitHub"**
3. Authorize Render to access your GitHub

---

### **Step 2: Create Web Service from Dashboard**

1. Click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click **"Connect account"** if not connected
   - Find and select **`SMC_EcoDrop`** repository
   - Click **"Connect"**

---

### **Step 3: Configure Web Service**

Fill in the following settings:

#### **Basic Settings**
- **Name:** `ecodrop-web` (or your preference)
- **Region:** Choose closest to you
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Runtime:** `Python 3`

#### **Build & Deploy**
- **Build Command:** `chmod +x build.sh && ./build.sh`
- **Start Command:** `gunicorn ecodrop_project.wsgi:application`

#### **Plan**
- **Instance Type:** Select **Free**

---

### **Step 4: Add Environment Variables**

Scroll down to **"Environment Variables"** section and add these:

Click **"Add Environment Variable"** for each:

```
PYTHON_VERSION = 3.11.0
DEBUG = False
DJANGO_SECRET_KEY = 8laq0x(#(v-tkywyj87ka2b_n8tczc04u(v1hp+^7vie54v!8^
DJANGO_SUPERUSER_USERNAME = admin
DJANGO_SUPERUSER_EMAIL = admin@ecodrop.com
DJANGO_SUPERUSER_PASSWORD = Admin2025EcoDrop!
```

**⚠️ Change the superuser password to something secure!**

---

### **Step 5: Create PostgreSQL Database**

Before clicking "Create Web Service":

1. Open a new tab and go to Render Dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `ecodrop-db`
   - **Database:** `ecodrop`
   - **User:** `ecodrop_user`
   - **Region:** Same as web service
   - **Instance Type:** **Free**
4. Click **"Create Database"**
5. Wait for database to be ready (~2 minutes)

---

### **Step 6: Connect Database to Web Service**

Back in your Web Service configuration:

1. Scroll to **Environment Variables**
2. Click **"Add Environment Variable"**
3. **Key:** `DATABASE_URL`
4. Click **"Add from Database"**
5. Select your database: **`ecodrop-db`**
6. Choose property: **Internal Database URL**
7. Click **"Add"**

---

### **Step 7: Deploy!**

1. Click **"Create Web Service"** at the bottom
2. Render will start building your application
3. Watch the logs in real-time

**Build process will:**
- ✅ Install dependencies
- ✅ Collect static files
- ✅ Run migrations
- ✅ **Create superuser automatically**
- ✅ Start your application

**Build time:** ~3-5 minutes

---

### **Step 8: Get Your URL**

Once deployed (status shows "Live"):

1. Find your app URL at the top (e.g., `ecodrop-web.onrender.com`)
2. Click on it to open your application

---

### **Step 9: Update Django Settings**

After getting your Render URL, update `settings.py`:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://ecodrop-web.onrender.com',  # Add your Render URL
    'https://ecodrop.ccshub.uk',
    'http://localhost:8000',
]

ALLOWED_HOSTS = ['ecodrop-web.onrender.com', '*']
```

Commit and push to GitHub:

```bash
git add ecodrop_project/settings.py
git commit -m "Add Render domain to settings"
git push origin main
```

Render will automatically redeploy!

---

## ✅ Access Your Application

After successful deployment:

- **Main App:** `https://ecodrop-web.onrender.com/`
- **Admin Panel:** `https://ecodrop-web.onrender.com/admin`

**Login with:**
- Username: `admin` (or what you set)
- Password: (what you set in `DJANGO_SUPERUSER_PASSWORD`)

---

## 📊 What Was Created

| File | Purpose |
|------|---------|
| **`render.yaml`** | Render configuration (optional, for infrastructure as code) |
| **`build.sh`** | Build script with superuser creation |
| **`Procfile`** | Defines start command |
| **`runtime.txt`** | Python version |
| **`requirements.txt`** | Python dependencies |

---

## 🔧 Render Free Tier Limits

- **512 MB RAM**
- **Free SSL** (automatic HTTPS)
- **Automatic deploys** from GitHub
- **PostgreSQL:** 1GB storage, 97 connection limit
- **Sleeps after 15 min inactivity** (wakes on request)

⚠️ **Note:** Free tier apps "sleep" after 15 minutes of inactivity. First request after sleeping takes ~30 seconds to wake up.

---

## 🐛 Troubleshooting

### Build Fails

**Check build logs:**
1. Click on your service
2. Go to "Logs" tab
3. Look for error messages

**Common issues:**
- Missing environment variables → Add in Environment section
- Database not connected → Check DATABASE_URL
- Build timeout → Free tier has limits, reduce dependencies

### App Crashes

**Check runtime logs:**
1. Go to "Logs" tab
2. Look for Python errors
3. Common fixes:
   - Ensure `DEBUG=False`
   - Check database migrations ran
   - Verify environment variables

### Static Files Not Loading

1. Check build logs for `collectstatic` success
2. Verify Whitenoise in `MIDDLEWARE`
3. Clear browser cache
4. Check `STATIC_ROOT` in settings

### Database Connection Errors

1. Verify PostgreSQL database is "Available"
2. Check `DATABASE_URL` environment variable
3. Ensure database is in same region as web service

---

## 🔄 Auto-Deployment

Every time you push to GitHub `main` branch:
1. Render detects the push
2. Automatically rebuilds your app
3. Runs migrations
4. Redeploys

**No manual steps needed!** 🎉

---

## 📱 Custom Domain (Optional)

Free tier supports custom domains:

1. Go to your service → "Settings"
2. Scroll to "Custom Domain"
3. Click "Add Custom Domain"
4. Follow DNS setup instructions

---

## 🆙 Upgrading

If you need more resources:
- **Starter Plan:** $7/month - No sleep, better performance
- **Standard Plan:** $25/month - More RAM, better compute

---

## 🔐 Security Best Practices

✅ **DO:**
- Use strong `DJANGO_SECRET_KEY`
- Set `DEBUG=False` in production
- Use strong superuser passwords
- Keep environment variables secret

❌ **DON'T:**
- Commit `.env` files to Git
- Use default passwords
- Enable DEBUG in production
- Hardcode secrets in code

---

## 📞 Need Help?

- **Render Docs:** https://render.com/docs
- **Django Deployment:** https://docs.djangoproject.com/en/4.2/howto/deployment/
- **Render Community:** https://community.render.com/

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] PostgreSQL database created
- [ ] Web service configured
- [ ] Environment variables set
- [ ] Database connected
- [ ] Build successful
- [ ] App is "Live"
- [ ] Can access main page
- [ ] Can log into admin panel
- [ ] CSRF_TRUSTED_ORIGINS updated

---

**🎉 Congratulations! Your EcoDrop app is now live on Render!**

Access your app at: `https://your-app.onrender.com`
