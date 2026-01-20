#!/usr/bin/env python
"""
Reset admin password
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecodrop_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Reset admin password
username = 'admin'
new_password = 'admin123'

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()
    print(f'Password reset successfully for user: {username}')
    print(f'')
    print(f'=== LOGIN CREDENTIALS ===')
    print(f'Username: {username}')
    print(f'Password: {new_password}')
    print(f'Email: {user.email}')
    print(f'=========================')
    print(f'')
    print(f'You can now log in at: http://127.0.0.1:8000/login/')
    print(f'Or Django admin at: http://127.0.0.1:8000/admin/')
except User.DoesNotExist:
    print(f'User {username} does not exist.')
