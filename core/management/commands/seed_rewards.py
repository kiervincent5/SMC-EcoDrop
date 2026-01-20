from django.core.management.base import BaseCommand
from core.models import RewardItem

SAMPLE_REWARDS = [
    {"reward_name": "Cafeteria Voucher", "points_required": 100, "icon": "🍽️"},
    {"reward_name": "School Merchandise", "points_required": 250, "icon": "🎒"},
    {"reward_name": "Library Privilege Pass", "points_required": 150, "icon": "📚"},
    {"reward_name": "EcoBottle", "points_required": 200, "icon": "🍼"},
    {"reward_name": "Gym Day Pass", "points_required": 180, "icon": "🏋️"},
]

class Command(BaseCommand):
    help = "Seed the database with sample RewardItem entries for development/testing."

    def handle(self, *args, **options):
        created_count = 0
        for data in SAMPLE_REWARDS:
            obj, created = RewardItem.objects.get_or_create(
                reward_name=data["reward_name"],
                defaults={
                    "points_required": data["points_required"],
                    "icon": data.get("icon", "🏆"),
                },
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"Seed complete. {created_count} reward(s) created, {len(SAMPLE_REWARDS) - created_count} existed."))
