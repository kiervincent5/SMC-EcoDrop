#!/usr/bin/env python
"""
Create superuser for Railway deployment
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecodrop_project.settings')
django.setup()

from django.contrib.auth import get_user_model

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
