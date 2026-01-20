#!/usr/bin/env bash
# Render Build Script with Automatic Superuser Creation

set -o errexit  # Exit on error

echo "🚀 Starting Render build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --no-input

# Create superuser automatically if credentials are provided
echo "👤 Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()

# Get credentials from environment variables
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@ecodrop.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

# Create superuser if it doesn't exist
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'✅ Superuser "{username}" created successfully!')
else:
    print(f'ℹ️  Superuser "{username}" already exists.')
END

echo "✅ Build complete!"
