#!/usr/bin/env python
"""
Setup script for EcoDrop Django project.
Run this after installing Python and Django to set up the database and sample data.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_project():
    """Setup the Django project with migrations and sample data"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecodrop_project.settings')
    django.setup()
    
    print("🌱 Setting up EcoDrop project...")
    
    # Run migrations
    print("📦 Creating database tables...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Setup sample data
    print("🎯 Creating sample data...")
    execute_from_command_line(['manage.py', 'setup_sample_data'])
    
    print("✅ Setup complete!")
    print("\n🚀 To start the server, run:")
    print("   python manage.py runserver")
    print("\n🔑 Login credentials:")
    print("   Admin: admin / admin")
    print("   Student: student123 / password123")

if __name__ == '__main__':
    setup_project()
