# ======================================================================
# core/admin.py
# This file configures the Django admin interface for your models.
# ======================================================================

from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, Entry, RewardItem, RedeemedPoints, Device, DeviceLog
import uuid

# Register your models here so they appear in the admin interface

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_id', 'user_type', 'total_points')
    search_fields = ('user__username', 'user__email', 'school_id', 'qr_code_data')
    list_filter = ('user_type', 'total_points')
    # school_id is FULLY EDITABLE - not in readonly_fields
    fields = ('user', 'school_id', 'user_type', 'id_generation_helper', 'total_points', 'qr_code_data')
    readonly_fields = ('id_generation_helper',)
    
    def id_generation_helper(self, obj):
        """Display helper text for ID generation"""
        if obj.user_type == 'student':
            suggested_id = UserProfile.generate_school_id()
            return format_html(
                '<div style="background: #e7f3ff; padding: 10px; border-radius: 5px;">'
                '<strong>📋 Student ID Format:</strong> C22-0369<br>'
                '<small>C = class, 22 = enrollment year, 0369 = student number</small><br><br>'
                '<strong>💡 Suggested ID:</strong> <code>{}</code><br>'
                '<small>You can manually enter any ID in the "Student id" field above</small>'
                '</div>',
                suggested_id
            )
        elif obj.user_type == 'teacher':
            suggested_id = UserProfile.generate_faculty_id()
            return format_html(
                '<div style="background: #fff3e7; padding: 10px; border-radius: 5px;">'
                '<strong>📋 Faculty ID Format:</strong> SMCIC-001-0001<br>'
                '<small>SMCIC = institution, 001 = department, 0001 = faculty number</small><br><br>'
                '<strong>💡 Suggested ID:</strong> <code>{}</code><br>'
                '<small>You can manually enter any ID in the "Student id" field above</small>'
                '</div>',
                suggested_id
            )
        else:
            return format_html(
                '<div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">'
                '<small>ID generation helpers are for students and teachers only</small>'
                '</div>'
            )
    
    id_generation_helper.short_description = "ID Generation Helper (Optional)"

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'no_bottle', 'points', 'created_at')
    list_filter = ('created_at', 'points')
    search_fields = ('user_profile__user__username',)
    date_hierarchy = 'created_at'

@admin.register(RewardItem)
class RewardItemAdmin(admin.ModelAdmin):
    list_display = ('reward_name', 'points_required', 'image')
    list_filter = ('points_required',)
    search_fields = ('reward_name',)

@admin.register(RedeemedPoints)
class RedeemedPointsAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'reward_item', 'redeemed_points', 'created_at')
    list_filter = ('created_at', 'reward_item')
    search_fields = ('user_profile__user__username', 'reward_item__reward_name')
    date_hierarchy = 'created_at'

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'device_id', 'location', 'status', 'total_bottles_processed', 'last_heartbeat')
    list_filter = ('status', 'created_at', 'last_heartbeat')
    search_fields = ('device_name', 'device_id', 'location')
    readonly_fields = ('api_key', 'total_bottles_processed', 'last_heartbeat', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new device
            obj.api_key = str(uuid.uuid4())
        super().save_model(request, obj, form, change)

@admin.register(DeviceLog)
class DeviceLogAdmin(admin.ModelAdmin):
    list_display = ('device', 'log_type', 'sort_result', 'message', 'created_at')
    list_filter = ('log_type', 'sort_result', 'created_at', 'device')
    search_fields = ('device__device_name', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically, not manually
