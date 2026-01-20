# ======================================================================
# core/urls.py
# This file maps your URLs to your view functions.
# You will need to create this file inside your 'core' app folder.
# ======================================================================

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Landing page
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher-profile/', views.teacher_profile_view, name='teacher_profile'),
    path('student-profile/', views.student_profile_view, name='student_profile'),
    path('rewards/', views.rewards_view, name='rewards'),
    path('rewards/history/', views.redemption_history_view, name='redemption_history'),
    path('redeem/<int:reward_id>/', views.redeem_reward_view, name='redeem_reward'),
    
    # URL for the admin dashboard (can be expanded later)
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin_panel/', views.admin_full_panel_view, name='admin_full_panel'),

    # Custom admin management pages (quick actions) - use 'console/' to avoid conflict with Django admin
    path('console/manage-users/', views.admin_manage_users_view, name='admin_users'),
    path('console/manage-users/add/', views.admin_user_add_view, name='admin_user_add'),
    path('console/manage-users/<int:user_id>/', views.admin_user_edit_view, name='admin_user_edit'),
    path('console/manage-rewards/', views.admin_manage_rewards_view, name='admin_rewards'),
    path('console/manage-rewards/add/', views.admin_reward_add_view, name='admin_reward_add'),
    path('console/manage-rewards/<int:reward_id>/', views.admin_reward_edit_view, name='admin_reward_edit'),
    path('console/manage-rewards/<int:reward_id>/delete/', views.admin_reward_delete_view, name='admin_reward_delete'),
    path('console/redemption-history/', views.admin_redemptions_view, name='admin_redemptions'),
    path('console/manage-devices/', views.admin_manage_devices_view, name='admin_devices'),
    path('console/manage-devices/<int:device_id>/', views.admin_device_edit_view, name='admin_device_edit'),
    path('console/manage-devices/add/', views.admin_device_add_view, name='admin_device_add'),
    path('console/transactions/', views.admin_transactions_view, name='admin_transactions'),
    path('console/device-logs/', views.admin_device_logs_view, name='admin_device_logs'),
    path('console/settings/', views.admin_settings_view, name='admin_settings'),
    path('console/debug-qr-codes/', views.debug_qr_codes_view, name='debug_qr_codes'),
    path('generate-qr-code/', views.generate_qr_code_view, name='generate_qr_code'),
    path('download-id-card/<int:user_id>/', views.download_id_card_view, name='download_id_card'),
    
    # API Endpoints for IoT device integration
    path('api/deposit/', views.api_deposit_view, name='api_deposit'),  # Legacy endpoint
    path('api/device/heartbeat/', views.api_device_heartbeat, name='api_device_heartbeat'),
    path('api/device/detection/', views.api_bottle_detection, name='api_bottle_detection'),
    path('api/device/error/', views.api_device_error, name='api_device_error'),
    path('api/user/verify/', views.api_user_verify, name='api_user_verify'),
]
