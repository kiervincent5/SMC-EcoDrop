from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, RewardItem

class Command(BaseCommand):
    help = 'Setup sample data for EcoDrop application'

    def handle(self, *args, **options):
        # Create sample reward items
        rewards = [
            {'name': 'Coffee Voucher', 'points': 50, 'icon': '☕'},
            {'name': 'School Supplies', 'points': 100, 'icon': '📚'},
            {'name': 'Lunch Voucher', 'points': 150, 'icon': '🍽️'},
            {'name': 'Movie Ticket', 'points': 200, 'icon': '🎬'},
            {'name': 'Gift Card', 'points': 500, 'icon': '🎁'},
        ]
        
        for reward_data in rewards:
            reward, created = RewardItem.objects.get_or_create(
                reward_name=reward_data['name'],
                defaults={
                    'points_required': reward_data['points'],
                    'icon': reward_data['icon']
                }
            )
            if created:
                self.stdout.write(f'Created reward: {reward.reward_name}')
        
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@ecodrop.com',
                password='admin',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('Created admin user (username: admin, password: admin)')
        
        # Create sample student user
        if not User.objects.filter(username='student123').exists():
            student_user = User.objects.create_user(
                username='student123',
                email='student123@smc.edu',
                password='password123',
                first_name='John',
                last_name='Doe'
            )
            self.stdout.write('Created sample student user (username: student123, password: password123)')
        
        self.stdout.write(self.style.SUCCESS('Sample data setup completed!'))
