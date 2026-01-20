# ======================================================================
# core/models.py
# This file defines your database structure based on your ERD.
# I've added the suggested 'total_points' field to the UserProfile
# for better performance.
# ======================================================================

from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Extends Django's built-in User model to include points
class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_points = models.PositiveIntegerField(default=0)
    # School ID Number - Works for ALL user types (students, teachers, admins)
    # Format: C22-0369 for students (C=class, 22=year, 0369=student number)
    # Format: SMCIC-***-**** for faculty/teachers
    school_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="School ID (Students: C22-0369 | Faculty: SMCIC-001-0001)",
        verbose_name="School ID Number"
    )
    # Keep the old field for backward compatibility
    qr_code_data = models.CharField(max_length=100, unique=True, blank=True, null=True)
    # User type field to distinguish between student, teacher, and admin
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')

    def __str__(self):
        return self.user.username
    
    @staticmethod
    def generate_student_id(year=None):
        """
        Generate a student ID in format: C22-0369
        C = class, 22 = year, 0369 = sequential number
        This is OPTIONAL - admins can manually enter any ID
        """
        if year is None:
            year = datetime.now().year % 100  # Get last 2 digits of year
        
        # Get the last student ID for this year
        last_student = UserProfile.objects.filter(
            user_type='student',
            school_id__startswith=f'C{year:02d}-'
        ).order_by('-school_id').first()
        
        if last_student and last_student.school_id:
            try:
                last_number = int(last_student.school_id.split('-')[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                next_number = 1
        else:
            next_number = 1
        
        return f'C{year:02d}-{next_number:04d}'
    
    @staticmethod
    def generate_faculty_id():
        """
        Generate a faculty ID in format: SMCIC-001-0001
        This is OPTIONAL - admins can manually enter any ID
        """
        # Get the last faculty ID
        last_faculty = UserProfile.objects.filter(
            user_type='teacher',
            school_id__startswith='SMCIC-'
        ).order_by('-school_id').first()
        
        if last_faculty and last_faculty.school_id:
            try:
                parts = last_faculty.school_id.split('-')
                if len(parts) >= 3:
                    dept_num = int(parts[1])
                    seq_num = int(parts[2])
                    seq_num += 1
                    if seq_num > 9999:
                        dept_num += 1
                        seq_num = 1
                    return f'SMCIC-{dept_num:03d}-{seq_num:04d}'
            except (IndexError, ValueError):
                pass
        
        return 'SMCIC-001-0001'
    
    def save(self, *args, **kwargs):
        """
        Override save to optionally auto-generate ID if not provided
        Admin can still manually set the ID
        """
        # Only auto-generate if school_id is empty and user wants it
        # This is OPTIONAL - can be skipped
        if not self.school_id:
            if self.user_type == 'student':
                # Uncomment next line if you want auto-generation by default
                # self.school_id = self.generate_student_id()
                pass  # Leave empty - admin will fill it manually
            elif self.user_type == 'teacher':
                # Uncomment next line if you want auto-generation by default
                # self.school_id = self.generate_faculty_id()
                pass  # Leave empty - admin will fill it manually
        
        super().save(*args, **kwargs)

# A record of a bottle deposit transaction
class Entry(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    no_bottle = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.points} points"

# A record of a reward that can be redeemed
class RewardItem(models.Model):
    reward_name = models.CharField(max_length=100)
    points_required = models.PositiveIntegerField()
    # You can add quantity or status if needed
    # quantity = models.PositiveIntegerField(default=100)
    # is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='rewards/', null=True, blank=True) # Image for reward icon

    def __str__(self):
        return self.reward_name

# A record of when a user redeems their points for a reward
class RedeemedPoints(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    reward_item = models.ForeignKey(RewardItem, on_delete=models.CASCADE)
    redeemed_points = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)  # Number of items redeemed
    receipt_number = models.CharField(max_length=30, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        qty_str = f" x{self.quantity}" if self.quantity > 1 else ""
        return f"{self.user_profile.user.username} redeemed {self.reward_item.reward_name}{qty_str}"
    
    def generate_receipt_number(self):
        """Generate unique receipt number like SMCEcoDrop-2025-10232145"""
        import random
        from django.utils import timezone
        
        now = timezone.now()
        year = now.strftime('%Y')
        date_time = now.strftime('%m%d%H%M')  # MMDDHHMI format
        
        while True:
            random_num = random.randint(10, 99)
            receipt_num = f"SMCEcoDrop-{year}-{date_time}{random_num}"
            if not RedeemedPoints.objects.filter(receipt_number=receipt_num).exists():
                return receipt_num
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)
    
    @property
    def valid_until(self):
        """Return date 3 days after redemption"""
        from datetime import timedelta
        return self.created_at + timedelta(days=3)
    
    @property
    def is_expired(self):
        """Check if redemption has expired (more than 3 days)"""
        from django.utils import timezone
        return timezone.now() > self.valid_until

# Physical device management
class Device(models.Model):
    DEVICE_STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    device_id = models.CharField(max_length=50, unique=True)
    device_name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    api_key = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=DEVICE_STATUS_CHOICES, default='offline')
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    total_bottles_processed = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.device_name} ({self.device_id})"

# Device activity logs
class DeviceLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('bottle_detected', 'Bottle Detected'),
        ('bottle_sorted', 'Bottle Sorted'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
        ('heartbeat', 'Heartbeat'),
    ]
    
    SORT_RESULT_CHOICES = [
        ('plastic', 'Plastic (Valid)'),
        ('invalid', 'Invalid (Not Plastic)'),
        ('error', 'Error'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    sort_result = models.CharField(max_length=10, choices=SORT_RESULT_CHOICES, null=True, blank=True)
    sensor_data = models.JSONField(null=True, blank=True)  # Store IR/CAP sensor readings
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_name} - {self.log_type} at {self.created_at}"
