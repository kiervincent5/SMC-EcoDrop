from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import uuid

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile when a new User is created"""
    if created:
        # Generate a unique QR code data for the user
        qr_code_data = f"SMC-USER-{instance.username}-{str(uuid.uuid4())[:8]}"
        UserProfile.objects.create(
            user=instance,
            qr_code_data=qr_code_data
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
