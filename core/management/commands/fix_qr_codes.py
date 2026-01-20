from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
import uuid

class Command(BaseCommand):
    help = 'Fix missing student IDs and QR codes for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--set-student-id',
            type=str,
            help='Set student ID for a specific username (format: username:school_id)',
        )

    def handle(self, *args, **options):
        if options['set_school_id']:
            # Set specific student ID
            try:
                username, school_id = options['set_school_id'].split(':')
                user = User.objects.get(username=username)
                user.profile.school_id = school_id
                user.profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Set student ID for {username}: {school_id}')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Format should be: --set-student-id username:school_id')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} not found')
                )
            return

        self.stdout.write("Checking user profiles...")
        
        # Get all users
        users = User.objects.all()
        fixed_count = 0
        
        for user in users:
            try:
                profile = user.profile
                
                # Set school_id to username if missing (default behavior)
                if not profile.school_id:
                    profile.school_id = user.username
                    profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Set student ID for {user.username}: {profile.school_id}')
                    )
                    fixed_count += 1
                
                # Show current status
                self.stdout.write(f'{user.username}: school_id={profile.school_id}, points={profile.total_points}')
                
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                UserProfile.objects.create(
                    user=user,
                    school_id=user.username,  # Default to username
                    qr_code_data=f"SMC-USER-{user.username}-{str(uuid.uuid4())[:8]}"
                )
                self.stdout.write(
                    self.style.WARNING(f'Created profile for {user.username} with school_id: {user.username}')
                )
                fixed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Fixed {fixed_count} users. Total users: {users.count()}')
        )
        
        self.stdout.write("\nTo set a specific student ID, use:")
        self.stdout.write("python manage.py fix_qr_codes --set-student-id username:school_id_number")
