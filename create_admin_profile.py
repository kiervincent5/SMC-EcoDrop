#!/usr/bin/env python
"""
Script to create UserProfile for admin user
Run this in Railway terminal or locally
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecodrop_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

# Get or create admin user
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@ecodrop.com',
        'is_staff': True,
        'is_superuser': True
    }
)

if not created:
    print(f"Admin user already exists: {admin_user.username}")
else:
    admin_user.set_password('admin123')
    admin_user.save()
    print(f"Created admin user: {admin_user.username}")

# Create or update UserProfile for admin
profile, profile_created = UserProfile.objects.get_or_create(
    user=admin_user,
    defaults={
        'school_id': 'ADMIN001',
        'user_type': 'admin',
        'points': 0
    }
)

if profile_created:
    print(f"✅ Created UserProfile for admin with ID: ADMIN001")
else:
    # Update existing profile
    profile.school_id = 'ADMIN001'
    profile.user_type = 'admin'
    profile.save()
    print(f"✅ Updated UserProfile for admin with ID: ADMIN001")

print("\nNow admin can login at /login/ with:")
print("ID Number: ADMIN001")
print("Password: admin123")
