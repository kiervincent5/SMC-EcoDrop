from django.core.management.base import BaseCommand
from core.models import Device

class Command(BaseCommand):
    help = 'Create the MOD01 device with the correct API key'

    def handle(self, *args, **options):
        device_id = "MOD01"
        api_key = "3794f230-dcac-4ae9-ad26-279383a7151f"
        
        # Check if device already exists
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_name': 'EcoDrop Device 1',
                'location': 'SMC Campus',
                'api_key': api_key,
                'status': 'online'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created device {device_id} with API key: {api_key}')
            )
        else:
            # Update the API key if device exists but key is different
            if device.api_key != api_key:
                device.api_key = api_key
                device.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated API key for existing device {device_id}')
                )
            else:
                self.stdout.write(f'Device {device_id} already exists with correct API key')
        
        self.stdout.write(f'Device: {device.device_name}')
        self.stdout.write(f'Location: {device.location}')
        self.stdout.write(f'API Key: {device.api_key}')
        self.stdout.write(f'Status: {device.status}')
