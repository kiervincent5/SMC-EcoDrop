from django.core.management.base import BaseCommand
from core.models import UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix user types for existing users'

    def handle(self, *args, **options):
        # Update all user types based on their current status
        for user in User.objects.all():
            profile = user.profile
            
            if user.is_superuser:
                profile.user_type = 'admin'
                self.stdout.write(self.style.SUCCESS(f"Set {user.username} as admin"))
            elif user.is_staff:
                # Check if they have a faculty ID (SMCIC-)
                if profile.school_id and profile.school_id.startswith('SMCIC'):
                    profile.user_type = 'teacher'
                    self.stdout.write(self.style.SUCCESS(f"Set {user.username} as teacher (has faculty ID)"))
                else:
                    # Staff without faculty ID - likely teacher
                    profile.user_type = 'teacher'
                    self.stdout.write(self.style.SUCCESS(f"Set {user.username} as teacher"))
            else:
                profile.user_type = 'student'
                self.stdout.write(self.style.SUCCESS(f"Set {user.username} as student"))
            
            profile.save()

        self.stdout.write(self.style.SUCCESS('\nDone! All user types updated.'))
