# 🚂 EcoDrop Railway Deployment Guide

This guide walks you through deploying the EcoDrop application to Railway.

## Prerequisites

- A [Railway](https://railway.app) account (free tier available)
- A [GitHub](https://github.com) account
- A [Cloudinary](https://cloudinary.com) account for media file storage (free tier available)

## Part 1: Push to GitHub

### Step 1: Initialize Git Repository (if not already done)

```bash
cd c:\Users\Admin\Desktop\SMC_EcoDrop_renderrrr
git init
git add .
git commit -m "Initial commit - EcoDrop project ready for Railway deployment"
```

### Step 2: Add GitHub Remote and Push

```bash
git remote add origin https://github.com/kodzuken-ai/ecodrop.git
git branch -M main
git push -u origin main
```

When prompted, use your GitHub credentials:
- **Username**: `kodzuken-ai`
- **Email**: `darrelcapadiso.casenas@my.smciligan.edu.ph`

## Part 2: Set Up Cloudinary (Media File Storage)

1. Go to [Cloudinary](https://cloudinary.com) and sign up for a free account
2. After logging in, go to your Dashboard
3. Copy the following values:
   - **Cloud Name**
   - **API Key**
   - **API Secret**
4. Keep these values handy - you'll need them for Railway environment variables

## Part 3: Deploy to Railway

### Step 1: Create New Project on Railway

1. Go to [Railway](https://railway.app) and log in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if not already connected
5. Select the **`kodzuken-ai/ecodrop`** repository

### Step 2: Add PostgreSQL Database

1. In your Railway project dashboard, click **"New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically create a PostgreSQL database
4. The `DATABASE_URL` environment variable will be automatically added to your project

### Step 3: Configure Environment Variables

1. Click on your **web service** (the Django app)
2. Go to the **"Variables"** tab
3. Add the following environment variables:

#### Required Variables:

```env
DJANGO_SECRET_KEY=<generate-a-random-secret-key>
DEBUG=False
SECURE_SSL_REDIRECT=False
```

**To generate a secure secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Cloudinary Variables (for media files):

```env
CLOUDINARY_CLOUD_NAME=<your-cloudinary-cloud-name>
CLOUDINARY_API_KEY=<your-cloudinary-api-key>
CLOUDINARY_API_SECRET=<your-cloudinary-api-secret>
```

#### Optional - Auto-create Superuser:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@ecodrop.com
DJANGO_SUPERUSER_PASSWORD=<your-secure-password>
```

### Step 4: Deploy!

1. Railway will automatically detect your Django app and start building
2. The build process will:
   - Install Python dependencies from `requirements.txt`
   - Collect static files
   - Run database migrations
   - Start the Gunicorn server

3. Monitor the deployment in the **"Deployments"** tab
4. Once complete, Railway will provide you with a public URL (e.g., `https://ecodrop-production.up.railway.app`)

### Step 5: Generate a Custom Domain (Optional)

1. In your Railway project, click on **"Settings"**
2. Scroll to **"Networking"** → **"Public Networking"**
3. Click **"Generate Domain"**
4. Railway will provide you with a `*.railway.app` domain
5. You can also add a custom domain if you have one

## Part 4: Post-Deployment Setup

### Create Superuser (if not auto-created)

If you didn't set the superuser environment variables, create one manually:

1. Go to your Railway project
2. Click on the **web service**
3. Go to the **"Deployments"** tab
4. Click on the latest deployment
5. Open the **"Terminal"** or use Railway CLI:

```bash
python manage.py createsuperuser
```

### Access Your Application

1. **Main App**: `https://your-app.railway.app`
2. **Admin Panel**: `https://your-app.railway.app/admin`
3. **Student Dashboard**: `https://your-app.railway.app/dashboard/`
4. **Collector Dashboard**: `https://your-app.railway.app/collector/dashboard/`

### Configure IoT Devices

Update your Arduino/ESP32 code with your Railway URL:

```cpp
const char* serverUrl = "https://your-app.railway.app";
```

## Part 5: Monitoring & Maintenance

### View Logs

1. In Railway, click on your web service
2. Go to the **"Deployments"** tab
3. Click on a deployment to view real-time logs

### Update Your Application

To deploy updates:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Railway will automatically detect the changes and redeploy.

### Database Backups

Railway automatically backs up your PostgreSQL database. To manually backup:

1. Click on your PostgreSQL service
2. Go to the **"Data"** tab
3. Click **"Backup"** to create a manual backup

## Troubleshooting

### Issue: Static files not loading

**Solution**: Make sure `STATICFILES_STORAGE` is set correctly in `settings.py`:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Issue: Database connection errors

**Solution**: Verify that:
1. PostgreSQL service is running in Railway
2. `DATABASE_URL` environment variable is set
3. Database migrations have been run

### Issue: 502 Bad Gateway

**Solution**: Check the deployment logs for errors. Common causes:
- Missing environment variables
- Database connection issues
- Incorrect Procfile configuration

### Issue: CSRF verification failed

**Solution**: Add your Railway domain to `CSRF_TRUSTED_ORIGINS` in `settings.py`:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    # ... other origins
]
```

## Cost Estimation

Railway offers:
- **Hobby Plan**: $5/month with $5 free credit (enough for small projects)
- **Pro Plan**: $20/month for larger applications

For the EcoDrop project (1 web service + 1 PostgreSQL database):
- Estimated cost: ~$5-10/month depending on usage

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Cloudinary Django Integration](https://cloudinary.com/documentation/django_integration)

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Review Django logs in the Railway terminal
3. Consult the [Railway Discord community](https://discord.gg/railway)

---

**Deployment completed!** 🎉 Your EcoDrop application is now live on Railway.
