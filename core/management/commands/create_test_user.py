from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create a test user with a specific student ID for testing the QR scanner'

    def add_arguments(self, parser):
        parser.add_argument('school_id', type=str, help='Student ID to create (e.g., C22-0369)')
        parser.add_argument('--username', type=str, help='Username (defaults to school_id)')
        parser.add_argument('--first-name', type=str, default='Test', help='First name')
        parser.add_argument('--last-name', type=str, default='Student', help='Last name')
        parser.add_argument('--email', type=str, help='Email (optional)')
        parser.add_argument('--points', type=int, default=0, help='Initial points')
        parser.add_argument('--create-sample', action='store_true', help='Create sample users for testing')

    def handle(self, *args, **options):
        # Handle sample users creation
        if options['create_sample']:
            self.create_sample_users()
            return
            
        school_id = options['school_id'].upper()  # Ensure uppercase
        username = options['username'] or school_id.replace('-', '')  # Remove dash for username
        first_name = options['first_name']
        last_name = options['last_name']
        email = options['email'] or f"{username.lower()}@smc.edu"
        points = options['points']
        
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with username "{username}" already exists')
                )
                user = User.objects.get(username=username)
                # Update the student ID if different
                if user.profile.school_id != school_id:
                    user.profile.school_id = school_id
                    user.profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated student ID for {username}: {school_id}')
                    )
                return
            
            # Check if student ID already exists
            if UserProfile.objects.filter(school_id=school_id).exists():
                existing_profile = UserProfile.objects.get(school_id=school_id)
                self.stdout.write(
                    self.style.ERROR(f'Student ID "{school_id}" already exists for user: {existing_profile.user.username}')
                )
                return
            
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123',  # Default password for testing
                first_name=first_name,
                last_name=last_name
            )
            
            # Update the profile with student ID and points
            user.profile.school_id = school_id
            user.profile.total_points = points
            user.profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test user:')
            )
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Student ID: {school_id}')
            self.stdout.write(f'  Name: {first_name} {last_name}')
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Points: {points}')
            self.stdout.write(f'  Password: testpass123')
            self.stdout.write('')
            self.stdout.write('You can now test scanning this student ID with your Arduino device!')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {str(e)}')
            )
    
    def create_sample_users(self):
        """Create sample users with realistic student IDs"""
        sample_users = [
            {'school_id': 'C22-0369', 'first_name': 'John', 'last_name': 'Doe', 'points': 50},
            {'school_id': 'C23-0145', 'first_name': 'Jane', 'last_name': 'Smith', 'points': 75},
            {'school_id': 'C24-0892', 'first_name': 'Mike', 'last_name': 'Johnson', 'points': 30},
            {'school_id': 'C25-0001', 'first_name': 'Sarah', 'last_name': 'Wilson', 'points': 100},
            {'school_id': 'C21-0555', 'first_name': 'Alex', 'last_name': 'Brown', 'points': 25},
        ]
        
        created_count = 0
        for user_data in sample_users:
            try:
                school_id = user_data['school_id']
                username = school_id.replace('-', '').lower()  # c220369, c230145, etc.
                
                # Check if already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(f'User {username} already exists, skipping...')
                    continue
                    
                if UserProfile.objects.filter(school_id=school_id).exists():
                    self.stdout.write(f'Student ID {school_id} already exists, skipping...')
                    continue
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@smc.edu",
                    password='testpass123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                # Set student ID and points
                user.profile.school_id = school_id
                user.profile.total_points = user_data['points']
                user.profile.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {school_id} -> {user_data["first_name"]} {user_data["last_name"]} ({username})')
                )
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {user_data["school_id"]}: {str(e)}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} sample users!')
        )
        self.stdout.write('Test with these student IDs:')
        for user_data in sample_users:
            self.stdout.write(f'  - {user_data["school_id"]} ({user_data["first_name"]} {user_data["last_name"]})')
        self.stdout.write('')
        self.stdout.write('Default password for all users: testpass123')
