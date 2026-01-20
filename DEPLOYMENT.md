# EcoDrop Deployment Guide

## 🔐 Security Configuration

### 1. Generate a Secret Key

Run this command to generate a secure secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Set Environment Variables on Your Server

On your production server (ecodrop.ccshub.uk), set these environment variables:

```bash
export DJANGO_SECRET_KEY="your-generated-secret-key-here"
export DEBUG="False"
# Optional: Only set this to True if you want to force HTTPS redirects
# export SECURE_SSL_REDIRECT="False"
```

**Important**: `SECURE_SSL_REDIRECT` is disabled by default to prevent redirect loops. Only enable it after confirming your SSL/HTTPS setup is working correctly.

**For different hosting platforms:**

#### Railway.app / Heroku:
- Go to Settings → Variables
- Add: `DJANGO_SECRET_KEY` = `your-secret-key`
- Add: `DEBUG` = `False`

#### DigitalOcean / VPS:
Add to your `.bashrc` or `.profile`:
```bash
echo 'export DJANGO_SECRET_KEY="your-secret-key"' >> ~/.bashrc
echo 'export DEBUG="False"' >> ~/.bashrc
source ~/.bashrc
```

Or create a `.env` file and use `python-dotenv` package.

### 3. Static Files for Production

Install WhiteNoise for serving static files:

```bash
pip install whitenoise
```

Add to `settings.py` MIDDLEWARE (after SecurityMiddleware):
```python
'whitenoise.middleware.WhiteNoiseMiddleware',
```

Run collectstatic:
```bash
python manage.py collectstatic
```

### 4. Database Migration

On production server:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Security Checklist

✅ `DEBUG = False` in production (via environment variable)
✅ `SECRET_KEY` is unique and secret (via environment variable)
✅ `CSRF_TRUSTED_ORIGINS` includes your domain
✅ HTTPS is enabled (SSL certificate)
✅ `SECURE_SSL_REDIRECT = True` (automatically enabled when DEBUG=False)
✅ Static files are collected and served properly

## 🚀 Deployment Steps

1. **Push your code** to your hosting platform
2. **Set environment variables** (SECRET_KEY, DEBUG=False)
3. **Run migrations**: `python manage.py migrate`
4. **Collect static files**: `python manage.py collectstatic`
5. **Create superuser**: `python manage.py createsuperuser`
6. **Restart the application**

## 🔧 Testing Production Settings Locally

To test with production settings locally:

```bash
# Windows PowerShell
$env:DEBUG="False"
$env:DJANGO_SECRET_KEY="test-key-for-local-testing"
python manage.py runserver

# Linux/Mac
DEBUG=False DJANGO_SECRET_KEY="test-key" python manage.py runserver
```

## 📱 IoT Device Configuration

Update your Arduino code with the production domain:
```cpp
const char* serverName = "ecodrop.ccshub.uk";
const int serverPort = 443;  // HTTPS port
```

Make sure your API endpoints accept requests from the IoT device.

## 🆘 Troubleshooting

### CSRF Error
- Ensure `CSRF_TRUSTED_ORIGINS` includes your domain with `https://`
- Clear browser cookies and try again

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Ensure WhiteNoise is installed and configured

### 500 Internal Server Error
- Check server logs
- Verify environment variables are set
- Ensure database migrations are run
