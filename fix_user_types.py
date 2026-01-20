"""
Script to fix user types for existing users
Run this with: py manage.py shell < fix_user_types.py
"""
from core.models import UserProfile
from django.contrib.auth.models import User

# Update all user types based on their current status
for user in User.objects.all():
    profile = user.profile
    
    if user.is_superuser:
        profile.user_type = 'admin'
        print(f"Set {user.username} as admin")
    elif user.is_staff:
        # Check if they have a faculty ID (SMCIC-)
        if profile.school_id and profile.school_id.startswith('SMCIC'):
            profile.user_type = 'teacher'
            print(f"Set {user.username} as teacher (has faculty ID)")
        else:
            # Staff without faculty ID - likely teacher
            profile.user_type = 'teacher'
            print(f"Set {user.username} as teacher")
    else:
        profile.user_type = 'student'
        print(f"Set {user.username} as student")
    
    profile.save()

print("\nDone! All user types updated.")
