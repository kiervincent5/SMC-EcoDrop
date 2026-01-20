#!/usr/bin/env python
"""
Create superuser for EcoDrop
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecodrop_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import UserProfile

User = get_user_model()

# Create superuser credentials
username = 'admin'
email = 'admin@ecodrop.com'
password = 'admin123'
first_name = 'Admin'
last_name = 'User'

# Create superuser if it doesn't exist
if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(
        username=username, 
        email=email, 
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    print(f'Superuser "{username}" created successfully!')
    print(f'Username: {username}')
    print(f'Password: {password}')
    print(f'Email: {email}')
    
    # Create or update profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.user_type = 'admin'
    profile.school_id = 'ADMIN-001'
    profile.save()
    print(f'Admin profile created with ID: {profile.school_id}')
else:
    print(f'Superuser "{username}" already exists.')
    user = User.objects.get(username=username)
    print(f'Username: {username}')
    print(f'You may need to reset the password if you forgot it.')
