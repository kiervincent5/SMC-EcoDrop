# ======================================================================
# core/views.py
# This file contains the main logic for your application.
# Each function handles a different page or action.
# ======================================================================

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from .models import UserProfile, Entry, RewardItem, RedeemedPoints, Device, DeviceLog
from .forms import LoginForm, RegisterForm

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import json
import uuid
from .utils import (
    get_next_available_ids,
    authenticate_device,
    generate_barcode_buffer,
    generate_id_card_image,
)


def home_view(request):
    """Landing page for all users"""
    if request.user.is_authenticated:
        return redirect("dashboard")

    # Get some stats for the landing page
    total_users = UserProfile.objects.count()
    total_bottles = Entry.objects.aggregate(total=models.Sum("no_bottle"))["total"] or 0
    available_rewards = RewardItem.objects.count()
    context = {
        "total_users": total_users,
        "total_bottles": total_bottles,
        "available_rewards": available_rewards,
    }
    return render(request, "core/home.html", context)


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Welcome to EcoDrop, {user.first_name}! Your account has been created successfully.",
            )
            # Automatically log in the user after registration
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, "core/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_id_or_email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # Try to find the user by username, school_id, or email
            user = None

            # Method 1: Try authenticating with username directly
            user = authenticate(
                request, username=username_or_id_or_email, password=password
            )

            # Method 2: Try finding by school_id (ID Number)
            if user is None:
                try:
                    profile = UserProfile.objects.get(school_id=username_or_id_or_email)
                    user = authenticate(
                        request, username=profile.user.username, password=password
                    )
                except UserProfile.DoesNotExist:
                    pass

            # Method 3: Try finding by email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_id_or_email)
                    user = authenticate(
                        request, username=user_obj.username, password=password
                    )
                except User.DoesNotExist:
                    pass

            # If user found and authenticated, log them in
            if user is not None:
                login(request, user)
                if user.is_staff:
                    # Check if superuser (admin) or regular staff (teacher)
                    if user.is_superuser:
                        return redirect("admin_dashboard")
                    else:
                        return redirect("teacher_dashboard")
                return redirect("dashboard")
            else:
                messages.error(
                    request,
                    "Invalid ID Number/Username/Email or password. Please try again.",
                )
        else:
            messages.error(request, "Please fill in all required fields correctly.")
    else:
        form = LoginForm()
    return render(request, "core/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    """Dashboard for logged-in users - redirects teachers to teacher dashboard"""
    # Check if user is staff/teacher
    if request.user.is_staff:
        # Check if they're admin (has access to admin dashboard)
        if request.user.is_superuser:
            return redirect("admin_dashboard")
        # Otherwise, they're a teacher
        return redirect("teacher_dashboard")

    # Regular student dashboard
    user_profile = request.user.profile
    recent_entries = Entry.objects.filter(user_profile=user_profile).order_by(
        "-created_at"
    )[:10]
    total_bottles = (
        Entry.objects.filter(user_profile=user_profile).aggregate(
            total=models.Sum("no_bottle")
        )["total"]
        or 0
    )

    return render(
        request,
        "core/dashboard.html",
        {
            "user_profile": user_profile,
            "recent_entries": recent_entries,
            "total_bottles": total_bottles,
        },
    )


@login_required
def teacher_dashboard_view(request):
    """Dashboard for teachers/faculty"""
    if not request.user.is_staff:
        return redirect("dashboard")

    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    # Teacher's own stats
    user_profile = request.user.profile
    teacher_bottles = (
        Entry.objects.filter(user_profile=user_profile).aggregate(
            total=models.Sum("no_bottle")
        )["total"]
        or 0
    )
    teacher_points = user_profile.total_points

    # School-wide statistics
    total_students = User.objects.filter(is_staff=False).count()
    total_bottles_all = (
        Entry.objects.aggregate(total=models.Sum("no_bottle"))["total"] or 0
    )
    total_points_all = (
        UserProfile.objects.aggregate(total=models.Sum("total_points"))["total"] or 0
    )

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_deposits = Entry.objects.filter(created_at__gte=week_ago).count()

    # Top students
    top_students = UserProfile.objects.filter(user__is_staff=False).order_by(
        "-total_points"
    )[:10]

    # Recent transactions
    recent_transactions = Entry.objects.select_related("user_profile__user").order_by(
        "-created_at"
    )[:20]

    # Teacher's own recent entries
    recent_entries = Entry.objects.filter(user_profile=user_profile).order_by(
        "-created_at"
    )[:10]

    return render(
        request,
        "core/teacher_dashboard.html",
        {
            "user_profile": user_profile,
            "teacher_bottles": teacher_bottles,
            "teacher_points": teacher_points,
            "total_students": total_students,
            "total_bottles_all": total_bottles_all,
            "total_points_all": total_points_all,
            "recent_deposits": recent_deposits,
            "top_students": top_students,
            "recent_transactions": recent_transactions,
            "recent_entries": recent_entries,
        },
    )


@login_required
def teacher_profile_view(request):
    """Profile page for teachers"""
    if not request.user.is_staff or request.user.is_superuser:
        return redirect("dashboard")

    user_profile = request.user.profile
    teacher_bottles = (
        Entry.objects.filter(user_profile=user_profile).aggregate(
            total=models.Sum("no_bottle")
        )["total"]
        or 0
    )
    recent_entries = Entry.objects.filter(user_profile=user_profile).order_by(
        "-created_at"
    )[:10]

    return render(
        request,
        "core/teacher_profile.html",
        {
            "user_profile": user_profile,
            "teacher_bottles": teacher_bottles,
            "recent_entries": recent_entries,
        },
    )


@login_required
def student_profile_view(request):
    """Profile page for students"""
    if request.user.is_staff:
        return redirect("teacher_dashboard")

    from django.utils import timezone
    from datetime import timedelta

    user_profile = request.user.profile
    total_bottles = (
        Entry.objects.filter(user_profile=user_profile).aggregate(
            total=models.Sum("no_bottle")
        )["total"]
        or 0
    )
    recent_entries = Entry.objects.filter(user_profile=user_profile).order_by(
        "-created_at"
    )[:10]

    # Only show valid redemptions (within 3 days)
    three_days_ago = timezone.now() - timedelta(days=3)
    redemptions = RedeemedPoints.objects.filter(
        user_profile=user_profile, created_at__gte=three_days_ago
    ).order_by("-created_at")[:5]

    return render(
        request,
        "core/student_profile.html",
        {
            "user_profile": user_profile,
            "total_bottles": total_bottles,
            "recent_entries": recent_entries,
            "redemptions": redemptions,
        },
    )


@login_required
def rewards_view(request):
    """Display available rewards for redemption with search and pagination"""
    from django.core.paginator import Paginator
    from django.db.models import Q

    user_profile = request.user.profile

    # Get search query
    search_query = request.GET.get("search", "")

    # Filter rewards based on search
    rewards = RewardItem.objects.all().order_by("points_required")
    if search_query:
        rewards = rewards.filter(
            Q(reward_name__icontains=search_query)
            | Q(points_required__icontains=search_query)
        )

    # Paginate results (9 per page for 3x3 grid)
    paginator = Paginator(rewards, 9)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Get last redemption from session and clear it
    last_redemption = request.session.pop("last_redemption", None)

    return render(
        request,
        "core/rewards.html",
        {
            "rewards": page_obj,
            "user_profile": user_profile,
            "search_query": search_query,
            "page_obj": page_obj,
            "last_redemption": last_redemption,
        },
    )


@login_required
def redeem_reward_view(request, reward_id):
    reward = RewardItem.objects.get(id=reward_id)
    profile = request.user.profile

    # Get quantity from POST request (default to 1)
    quantity = 1
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            # Validate quantity is positive
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1

    # Calculate total points required
    total_points_required = reward.points_required * quantity

    if profile.total_points >= total_points_required:
        # Subtract total points
        profile.total_points -= total_points_required
        profile.save()

        # Create a redemption record with quantity
        redemption = RedeemedPoints.objects.create(
            user_profile=profile,
            reward_item=reward,
            redeemed_points=total_points_required,
            quantity=quantity,
        )

        # Calculate valid until date (3 days from now)
        from datetime import timedelta

        valid_until = redemption.created_at + timedelta(days=3)

        # Store redemption info in session for success modal
        request.session["last_redemption"] = {
            "reward_name": reward.reward_name,
            "reward_image": reward.image.url if reward.image else None,
            "points_deducted": total_points_required,
            "quantity": quantity,
            "redemption_date": redemption.created_at.strftime("%B %d, %Y"),
            "redemption_time": redemption.created_at.strftime("%I:%M %p"),
            "valid_until": valid_until.strftime("%B %d, %Y"),
            "receipt_number": redemption.receipt_number,
        }

    return redirect("rewards")


@login_required
def redemption_history_view(request):
    """Display user's redemption history (only valid/non-expired redemptions)"""
    from django.utils import timezone
    from datetime import timedelta
    from django.core.paginator import Paginator

    user_profile = request.user.profile

    # Only show redemptions from the last 3 days (valid redemptions)
    # Order by created_at ascending (oldest first) so items expiring soonest are at top
    three_days_ago = timezone.now() - timedelta(days=3)
    redemptions = (
        RedeemedPoints.objects.filter(
            user_profile=user_profile, created_at__gte=three_days_ago
        )
        .select_related("reward_item")
        .order_by("created_at")
    )  # Oldest first = expires soonest

    # Paginate results (10 per page)
    paginator = Paginator(redemptions, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/redemption_history.html",
        {
            "redemptions": page_obj,
            "user_profile": user_profile,
            "page_obj": page_obj,
        },
    )


@login_required
def admin_dashboard_view(request):
    # Ensure only staff/admins can access this page
    if not request.user.is_staff:
        return redirect("dashboard")

    # Comprehensive admin dashboard data
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta

    # User statistics
    total_users = UserProfile.objects.count()
    student_users = UserProfile.objects.filter(user__is_staff=False).count()
    faculty_users = UserProfile.objects.filter(user__is_staff=True).count()

    # Recycling statistics
    total_bottles = Entry.objects.aggregate(total=Sum("no_bottle"))["total"] or 0
    total_points_earned = Entry.objects.aggregate(total=Sum("points"))["total"] or 0
    total_points_redeemed = (
        RedeemedPoints.objects.aggregate(total=Sum("redeemed_points"))["total"] or 0
    )

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_deposits = Entry.objects.filter(created_at__gte=week_ago).count()
    recent_redemptions = RedeemedPoints.objects.filter(created_at__gte=week_ago).count()

    # Top recyclers
    top_recyclers = UserProfile.objects.order_by("-total_points")[:5]

    # Recent transactions
    recent_transactions = Entry.objects.select_related("user_profile__user").order_by(
        "-created_at"
    )[:10]

    # Reward statistics
    reward_stats = (
        RedeemedPoints.objects.values("reward_item__reward_name")
        .annotate(count=Count("id"), total_points=Sum("redeemed_points"))
        .order_by("-count")[:5]
    )

    # Average points per user
    avg_points_per_user = (
        UserProfile.objects.aggregate(avg=Avg("total_points"))["avg"] or 0
    )

    # Device statistics
    total_devices = Device.objects.count()
    online_devices = Device.objects.filter(status="online").count()
    offline_devices = Device.objects.filter(status="offline").count()
    error_devices = Device.objects.filter(status="error").count()
    maintenance_devices = Device.objects.filter(status="maintenance").count()

    # Recent device activity
    recent_device_logs = DeviceLog.objects.select_related("device").order_by(
        "-created_at"
    )[:10]

    # Device performance data
    device_performance = Device.objects.annotate(
        recent_bottles=Count(
            "devicelog",
            filter=models.Q(
                devicelog__log_type="bottle_sorted", devicelog__created_at__gte=week_ago
            ),
        )
    ).order_by("-total_bottles_processed")[:5]

    # Basic user list for Manage Users section (no backend actions here)
    user_list = User.objects.select_related("profile").order_by("username")[:100]

    context = {
        "total_users": total_users,
        "student_users": student_users,
        "faculty_users": faculty_users,
        "total_bottles": total_bottles,
        "total_points_earned": total_points_earned,
        "total_points_redeemed": total_points_redeemed,
        "recent_deposits": recent_deposits,
        "recent_redemptions": recent_redemptions,
        "top_recyclers": top_recyclers,
        "recent_transactions": recent_transactions,
        "reward_stats": reward_stats,
        "avg_points_per_user": round(avg_points_per_user, 1),
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "error_devices": error_devices,
        "maintenance_devices": maintenance_devices,
        "recent_device_logs": recent_device_logs,
        "device_performance": device_performance,
        "user_list": user_list,
    }

    return render(request, "core/admin_dashboard.html", context)


@login_required
def admin_manage_users_view(request):
    # Ensure only staff/admins can access
    if not request.user.is_staff:
        return redirect("dashboard")

    users = User.objects.select_related("profile").order_by("username")
    student_count = UserProfile.objects.filter(user_type="student").count()
    faculty_count = UserProfile.objects.filter(user_type="teacher").count()

    return render(
        request,
        "core/admin_manage_users.html",
        {
            "users": users,
            "student_count": student_count,
            "faculty_count": faculty_count,
        },
    )


@login_required
def admin_manage_rewards_view(request):
    if not request.user.is_staff:
        return redirect("dashboard")

    # Handle POST requests for adding/editing rewards
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            reward_name = request.POST.get("reward_name")
            points_required = request.POST.get("points_required")
            icon = request.POST.get("icon", "🏆")

            if reward_name and points_required:
                RewardItem.objects.create(
                    reward_name=reward_name,
                    points_required=int(points_required),
                    icon=icon,
                )

        elif action == "edit":
            reward_id = request.POST.get("reward_id")
            reward_name = request.POST.get("reward_name")
            points_required = request.POST.get("points_required")
            icon = request.POST.get("icon", "🏆")

            if reward_id and reward_name and points_required:
                reward = RewardItem.objects.get(id=reward_id)
                reward.reward_name = reward_name
                reward.points_required = int(points_required)
                reward.icon = icon
                reward.save()

        elif action == "delete":
            reward_id = request.POST.get("reward_id")
            if reward_id:
                RewardItem.objects.filter(id=reward_id).delete()

        return redirect("admin_rewards")

    rewards = RewardItem.objects.all().order_by("points_required", "reward_name")
    return render(
        request,
        "core/admin_manage_rewards.html",
        {
            "rewards": rewards,
        },
    )


@login_required
def admin_reward_add_view(request):
    if not request.user.is_staff:
        return redirect("dashboard")
    if request.method == "POST":
        reward = RewardItem.objects.create(
            reward_name=request.POST.get("reward_name"),
            points_required=int(request.POST.get("points_required")),
        )
        # Handle image upload (now required)
        if request.FILES.get("image"):
            reward.image = request.FILES["image"]
            reward.save()
        return redirect("admin_rewards")
    return render(request, "core/admin_reward_add.html")


@login_required
def admin_reward_edit_view(request, reward_id):
    if not request.user.is_staff:
        return redirect("dashboard")
    try:
        reward = RewardItem.objects.get(id=reward_id)
    except RewardItem.DoesNotExist:
        return redirect("admin_rewards")

    if request.method == "POST":
        reward.reward_name = request.POST.get("reward_name")
        reward.points_required = int(request.POST.get("points_required"))
        # Handle image upload
        if request.FILES.get("image"):
            reward.image = request.FILES["image"]
        reward.save()
        return redirect("admin_rewards")
    return render(request, "core/admin_reward_edit.html", {"reward": reward})


@login_required
def admin_reward_delete_view(request, reward_id):
    if not request.user.is_staff:
        return redirect("dashboard")
    if request.method == "POST":
        RewardItem.objects.filter(id=reward_id).delete()
    return redirect("admin_rewards")


@login_required
def admin_redemptions_view(request):
    if not request.user.is_staff:
        return redirect("dashboard")
    redemptions = RedeemedPoints.objects.select_related(
        "user_profile__user", "reward_item"
    ).order_by("-created_at")[:100]
    return render(
        request,
        "core/admin_redemptions.html",
        {
            "redemptions": redemptions,
        },
    )


@login_required
def admin_manage_devices_view(request):
    if not request.user.is_staff:
        return redirect("dashboard")
    devices = Device.objects.all().order_by("device_name")
    return render(
        request,
        "core/admin_manage_devices.html",
        {
            "devices": devices,
        },
    )


@login_required
def admin_user_edit_view(request, user_id: int):
    if not request.user.is_staff:
        return redirect("dashboard")
    try:
        user_obj = User.objects.select_related("profile").get(id=user_id)
    except User.DoesNotExist:
        return redirect("admin_users")

    if request.method == "POST":
        # Basic fields
        user_obj.username = (
            request.POST.get("username", user_obj.username).strip() or user_obj.username
        )
        user_obj.first_name = request.POST.get("first_name", user_obj.first_name)
        user_obj.last_name = request.POST.get("last_name", user_obj.last_name)
        user_obj.email = request.POST.get("email", user_obj.email)
        user_obj.is_staff = True if request.POST.get("is_staff") == "on" else False
        # Profile points
        try:
            new_points = int(
                request.POST.get("total_points", user_obj.profile.total_points)
            )
            user_obj.profile.total_points = max(0, new_points)
        except Exception:
            pass
        # Student/Faculty ID - EDITABLE
        school_id = request.POST.get("school_id", "").strip()
        if school_id:
            user_obj.profile.school_id = school_id
        user_obj.save()
        user_obj.profile.save()
        return redirect("admin_users")

    return render(
        request,
        "core/admin_user_edit.html",
        {
            "u": user_obj,
        },
    )


@login_required
def admin_device_edit_view(request, device_id: int):
    if not request.user.is_staff:
        return redirect("dashboard")
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return redirect("admin_devices")

    if request.method == "POST":
        device.device_name = (
            request.POST.get("name", device.device_name).strip() or device.device_name
        )
        device.device_id = (
            request.POST.get("device_id", device.device_id).strip() or device.device_id
        )
        device.location = request.POST.get("location", device.location)
        device.status = request.POST.get("status", device.status)
        try:
            device.total_bottles_processed = int(
                request.POST.get(
                    "total_bottles_processed", device.total_bottles_processed
                )
            )
        except Exception:
            pass
        device.save()
        return redirect("admin_devices")

    return render(
        request,
        "core/admin_device_edit.html",
        {
            "device": device,
        },
    )


@login_required
def admin_full_panel_view(request):
    """Full admin panel with all management options"""
    if not request.user.is_staff:
        return redirect("dashboard")
    return render(request, "core/admin_full_panel.html")


@login_required
def admin_user_add_view(request):
    """Add new user page"""
    if not request.user.is_staff:
        return redirect("dashboard")

    # Use utility helper to get next IDs
    next_school_id, next_faculty_id = get_next_available_ids()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        user_type = request.POST.get("user_type", "student")

        # Get student/faculty ID from form (EDITABLE - admin can change it)
        manual_school_id = request.POST.get("school_id", "").strip()
        manual_faculty_id = request.POST.get("faculty_id", "").strip()

        # Use manual ID if provided, otherwise auto-generate
        if user_type == "student":
            if manual_school_id:
                # Use the manually entered ID
                generated_id = manual_school_id
            else:
                # Auto-generate only if not provided
                last_student = (
                    UserProfile.objects.filter(
                        school_id__startswith=f"C{current_year}-"
                    )
                    .order_by("-school_id")
                    .first()
                )

                if last_student and last_student.school_id:
                    try:
                        last_num = int(last_student.school_id.split("-")[1])
                        generated_id = f"C{current_year}-{str(last_num + 1).zfill(4)}"
                    except:
                        generated_id = f"C{current_year}-0001"
                else:
                    generated_id = f"C{current_year}-0001"
        elif user_type == "teacher":
            if manual_faculty_id:
                # Use the manually entered ID
                generated_id = manual_faculty_id
            else:
                # Auto-generate only if not provided
                from datetime import datetime

                current_year_full = str(datetime.now().year)
                last_faculty = (
                    UserProfile.objects.filter(school_id__startswith="SMCIC-")
                    .order_by("-school_id")
                    .first()
                )

                if last_faculty and last_faculty.school_id:
                    try:
                        parts = last_faculty.school_id.split("-")
                        if len(parts) == 3:
                            last_num = int(parts[1])
                            generated_id = f"SMCIC-{str(last_num + 1).zfill(3)}-{current_year_full}"
                        else:
                            generated_id = f"SMCIC-001-{current_year_full}"
                    except:
                        generated_id = f"SMCIC-001-{current_year_full}"
                else:
                    generated_id = f"SMCIC-001-{current_year_full}"
        else:
            generated_id = None

        # Set is_staff based on user type
        is_staff = user_type in ["teacher", "staff"]

        if username and password:
            try:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    is_staff=is_staff,
                )
                # Get or create profile and update school_id and user_type
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.user_type = (
                    user_type  # Set user type (student, teacher, or staff)
                )
                if generated_id:
                    profile.school_id = generated_id
                    profile.qr_code_data = (
                        generated_id  # Set qr_code_data to same value as school_id
                    )
                profile.save()

                user_type_display = {
                    "student": "Student",
                    "teacher": "Teacher/Faculty",
                    "staff": "Staff/Admin",
                }.get(user_type, "User")
                messages.success(
                    request,
                    f'{user_type_display} {username} created successfully with ID: {generated_id if generated_id else "N/A"}',
                )
                return redirect("admin_users")
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")

    return render(
        request,
        "core/admin_user_add.html",
        {
            "next_school_id": next_school_id,
            "next_faculty_id": next_faculty_id,
        },
    )


@login_required
def admin_device_add_view(request):
    """Add new device page"""
    if not request.user.is_staff:
        return redirect("dashboard")

    if request.method == "POST":
        device_name = request.POST.get("device_name", "").strip()
        location = request.POST.get("location", "").strip()

        if device_name and location:
            api_key = str(uuid.uuid4())
            Device.objects.create(
                device_name=device_name,
                location=location,
                api_key=api_key,
                status="offline",
            )
            messages.success(request, f"Device {device_name} created successfully!")
            return redirect("admin_devices")

    return render(request, "core/admin_device_add.html")


@login_required
def admin_transactions_view(request):
    """View all transactions"""
    if not request.user.is_staff:
        return redirect("dashboard")
    transactions = Entry.objects.select_related("user_profile__user").order_by(
        "-created_at"
    )[:200]
    return render(
        request,
        "core/admin_transactions.html",
        {
            "transactions": transactions,
        },
    )


@login_required
def admin_device_logs_view(request):
    """View device activity logs"""
    if not request.user.is_staff:
        return redirect("dashboard")
    logs = DeviceLog.objects.select_related("device").order_by("-created_at")[:200]
    return render(
        request,
        "core/admin_device_logs.html",
        {
            "logs": logs,
        },
    )


@login_required
def admin_settings_view(request):
    """System settings page"""
    if not request.user.is_staff:
        return redirect("dashboard")
    import django

    return render(
        request,
        "core/admin_settings.html",
        {
            "django_version": django.get_version(),
        },
    )


# --- API Views for IoT Device Integration ---


# Removed - now using version imported from .utils


@csrf_exempt
def api_device_heartbeat(request):
    """Device heartbeat endpoint to track device status"""
    if request.method == "POST":
        device = authenticate_device(request)
        if not device:
            return JsonResponse(
                {"status": "error", "message": "Invalid API key."}, status=401
            )

        try:
            data = json.loads(request.body)

            # Update device status and heartbeat
            device.status = data.get("status", "online")
            device.last_heartbeat = timezone.now()
            device.save()

            # Log heartbeat
            DeviceLog.objects.create(
                device=device,
                log_type="heartbeat",
                sensor_data=data.get("sensor_data"),
                message=f"Device {device.device_name} heartbeat",
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Heartbeat received",
                    "server_time": timezone.now().isoformat(),
                }
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse(
        {"status": "error", "message": "Invalid request method."}, status=405
    )


@csrf_exempt
def api_bottle_detection(request):
    """Endpoint for device to report bottle detection and sorting results"""
    if request.method == "POST":
        device = authenticate_device(request)
        if not device:
            return JsonResponse(
                {"status": "error", "message": "Invalid API key."}, status=401
            )

        try:
            data = json.loads(request.body)
            sort_result = data.get("sort_result")  # 'plastic', 'invalid', 'error'
            sensor_data = data.get("sensor_data", {})
            user_id = data.get("user_id")  # QR code data if bottle is valid plastic

            # Log the detection event
            DeviceLog.objects.create(
                device=device,
                log_type="bottle_detected",
                sort_result=sort_result,
                sensor_data=sensor_data,
                message=f"Bottle detected: {sort_result}",
            )

            # If plastic bottle and user identified, award points
            if sort_result == "plastic" and user_id:
                try:
                    profile = UserProfile.objects.get(qr_code_data=user_id)
                    points_earned = 10  # 10 points per plastic bottle

                    # Update user's total points
                    profile.total_points += points_earned
                    profile.save()

                    # Create entry record
                    Entry.objects.create(
                        user_profile=profile, no_bottle=1, points=points_earned
                    )

                    # Update device bottle count
                    device.total_bottles_processed += 1
                    device.save()

                    # Log successful sorting
                    DeviceLog.objects.create(
                        device=device,
                        log_type="bottle_sorted",
                        sort_result="plastic",
                        sensor_data=sensor_data,
                        message=f"Points awarded to {profile.user.username}",
                    )

                    return JsonResponse(
                        {
                            "status": "success",
                            "message": f"{points_earned} points awarded to {profile.user.username}",
                            "user_total_points": profile.total_points,
                        }
                    )

                except UserProfile.DoesNotExist:
                    return JsonResponse(
                        {
                            "status": "warning",
                            "message": "Plastic bottle detected but user not found",
                        }
                    )

            # For invalid bottles or no user ID
            return JsonResponse(
                {"status": "success", "message": f"Bottle processed: {sort_result}"}
            )

        except Exception as e:
            # Log error
            if device:
                DeviceLog.objects.create(
                    device=device, log_type="error", message=f"API Error: {str(e)}"
                )
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse(
        {"status": "error", "message": "Invalid request method."}, status=405
    )


@csrf_exempt
def api_device_error(request):
    """Endpoint for device to report errors"""
    if request.method == "POST":
        device = authenticate_device(request)
        if not device:
            return JsonResponse(
                {"status": "error", "message": "Invalid API key."}, status=401
            )

        try:
            data = json.loads(request.body)
            error_message = data.get("error_message", "Unknown error")
            error_code = data.get("error_code")

            # Update device status to error
            device.status = "error"
            device.save()

            # Log the error
            DeviceLog.objects.create(
                device=device,
                log_type="error",
                sensor_data=data.get("sensor_data"),
                message=f"Error {error_code}: {error_message}",
            )

            return JsonResponse({"status": "success", "message": "Error logged"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse(
        {"status": "error", "message": "Invalid request method."}, status=405
    )


@csrf_exempt
def api_user_verify(request):
    """Endpoint for device to verify user QR code"""
    if request.method == "GET":
        device = authenticate_device(request)
        if not device:
            return JsonResponse(
                {"status": "error", "message": "Invalid API key.", "ok": False},
                status=401,
            )

        try:
            code = request.GET.get("code")
            if not code:
                return JsonResponse(
                    {"status": "error", "message": "No code provided.", "ok": False},
                    status=400,
                )

                # Clean the student ID - handle format like "C22-0369" or "C220369" (without hyphen)
            clean_code = code.strip().upper()  # Convert to uppercase for consistency

            # Debug: Log the incoming student ID
            print(f"DEBUG: Received student ID: '{code}' -> cleaned: '{clean_code}'")

            # Try to find user by student ID first, then fallback to other methods
            profile = None
            lookup_method = None

            # Method 1: Look up by school_id field (exact match with hyphen)
            if not profile:
                try:
                    profile = UserProfile.objects.get(school_id=clean_code)
                    lookup_method = "school_id"
                    print(f"DEBUG: User found by school_id - {profile.user.username}")
                except UserProfile.DoesNotExist:
                    pass

            # Method 1b: If not found, try adding hyphen for student IDs (C250001 -> C25-0001)
            if (
                not profile
                and len(clean_code) >= 7
                and clean_code[0] == "C"
                and "-" not in clean_code
            ):
                try:
                    # Format: C + 2-digit year + 4-digit number (e.g., C250001 -> C25-0001)
                    formatted_code = f"{clean_code[:3]}-{clean_code[3:]}"
                    profile = UserProfile.objects.get(school_id=formatted_code)
                    lookup_method = "school_id_formatted"
                    print(
                        f"DEBUG: User found by formatted school_id ({formatted_code}) - {profile.user.username}"
                    )
                except (UserProfile.DoesNotExist, IndexError):
                    pass

                    # Method 1c: Try adding hyphen for faculty IDs (SMCIC1232025 -> SMCIC-123-2025)
            if not profile and clean_code.startswith("SMCIC") and "-" not in clean_code:
                try:
                    # Format: SMCIC + 3-digit number + 4-digit year (e.g., SMCIC1232025 -> SMCIC-123-2025)
                    if len(clean_code) == 12:  # SMCIC + 3 digits + 4 digits
                        formatted_code = f"SMCIC-{clean_code[5:8]}-{clean_code[8:]}"
                        profile = UserProfile.objects.get(school_id=formatted_code)
                        lookup_method = "faculty_id_formatted"
                        print(
                            f"DEBUG: User found by formatted faculty_id ({formatted_code}) - {profile.user.username}"
                        )
                except (UserProfile.DoesNotExist, IndexError):
                    pass

            # Method 2: Look up by school_id case-insensitive
            if not profile:
                try:
                    profile = UserProfile.objects.get(school_id__iexact=clean_code)
                    lookup_method = "school_id_case_insensitive"
                    print(
                        f"DEBUG: User found by school_id (case-insensitive) - {profile.user.username}"
                    )
                except UserProfile.DoesNotExist:
                    pass

            # Method 3: Look up by username (if student ID matches username)
            if not profile:
                try:
                    from django.contrib.auth.models import User

                    user = User.objects.get(username=clean_code)
                    profile = user.profile
                    lookup_method = "username"
                    # Set the school_id if it's missing
                    if not profile.school_id:
                        profile.school_id = clean_code
                        profile.save()
                        print(f"DEBUG: Auto-set school_id for {user.username}")
                    print(f"DEBUG: User found by username - {profile.user.username}")
                except (User.DoesNotExist, UserProfile.DoesNotExist):
                    pass

            # Method 4: Look up by old qr_code_data field (backward compatibility)
            if not profile:
                try:
                    profile = UserProfile.objects.get(qr_code_data=clean_code)
                    lookup_method = "qr_code_data"
                    print(
                        f"DEBUG: User found by qr_code_data - {profile.user.username}"
                    )
                except UserProfile.DoesNotExist:
                    pass

            if profile:
                # Log successful verification
                DeviceLog.objects.create(
                    device=device,
                    log_type="bottle_detected",  # Using existing log type
                    message=f"User {profile.user.username} verified with student ID '{clean_code}' via {lookup_method}",
                )

                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"User {profile.user.username} verified",
                        "ok": True,
                        "user": {
                            "username": profile.user.username,
                            "full_name": f"{profile.user.first_name} {profile.user.last_name}".strip(),
                            "total_points": profile.total_points,
                            "school_id": profile.school_id or clean_code,
                        },
                        "lookup_method": lookup_method,
                    }
                )

            # No user found - provide comprehensive debugging info
            print(f"DEBUG: No user found for student ID '{clean_code}'")

            # Get all existing student IDs and usernames for debugging
            all_school_ids = list(
                UserProfile.objects.exclude(school_id__isnull=True)
                .exclude(school_id="")
                .values_list("school_id", "user__username")
            )

            all_usernames = list(
                User.objects.values_list("username", flat=True)[:20]
            )  # Limit to 20

            print(f"DEBUG: All student IDs in database: {all_school_ids}")
            print(f"DEBUG: Sample usernames: {all_usernames}")

            # Log failed verification with detailed info
            DeviceLog.objects.create(
                device=device,
                log_type="error",
                message=f"Failed verification: student ID '{clean_code}' not found. Available: {[sid for sid, _ in all_school_ids[:10]]}",
            )

            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Student ID not found: {clean_code}",
                    "ok": False,
                    "debug": {
                        "received_school_id": clean_code,
                        "original_input": code,
                        "available_school_ids": [
                            sid for sid, username in all_school_ids
                        ],
                        "available_usernames": all_usernames,
                        "total_users": UserProfile.objects.count(),
                        "users_with_school_id": UserProfile.objects.exclude(
                            school_id__isnull=True
                        )
                        .exclude(school_id="")
                        .count(),
                    },
                }
            )

        except Exception as e:
            # Log error
            if device:
                DeviceLog.objects.create(
                    device=device,
                    log_type="error",
                    message=f"User verification API Error: {str(e)}",
                )
            print(f"ERROR in api_user_verify: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": str(e), "ok": False}, status=400
            )

    return JsonResponse(
        {"status": "error", "message": "Invalid request method.", "ok": False},
        status=405,
    )


@login_required
def debug_qr_codes_view(request):
    """Debug view to see all user QR codes"""
    if not request.user.is_staff:
        return redirect("dashboard")

    users_with_qr = UserProfile.objects.select_related("user").all()
    return render(
        request,
        "core/debug_qr_codes.html",
        {
            "users_with_qr": users_with_qr,
        },
    )


@login_required
def generate_qr_code_view(request):
    """Generate barcode for the logged-in user's student ID"""
    from django.http import HttpResponse

    user_profile = request.user.profile
    school_id = user_profile.school_id

    if not school_id:
        return HttpResponse("No Student ID found", status=404)

    try:
        buffer = generate_barcode_buffer(school_id)
        # Return as image
        response = HttpResponse(buffer, content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="{school_id}_barcode.png"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating barcode: {str(e)}", status=500)


@login_required
def download_id_card_view(request, user_id):
    """Generate and download ID card with photo, name, ID, and barcode"""
    from django.http import HttpResponse

    if not request.user.is_staff:
        return redirect("dashboard")

    try:
        user = User.objects.get(id=user_id)
        image_buffer = generate_id_card_image(user)

        response = HttpResponse(image_buffer, content_type="image/png")
        filename = f"{user.profile.school_id or 'Student'}_ID_Card.png"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating ID card: {str(e)}", status=500)


# Legacy API endpoint (kept for backward compatibility)
@csrf_exempt
def api_deposit_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            bottles = data.get("bottles", 1)

            profile = UserProfile.objects.get(qr_code_data=user_id)
            points_earned = bottles * 10

            profile.total_points += points_earned
            profile.save()

            Entry.objects.create(
                user_profile=profile, no_bottle=bottles, points=points_earned
            )

            return JsonResponse(
                {"status": "success", "message": f"{points_earned} points added."},
                status=201,
            )

        except UserProfile.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "User not found."}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse(
        {"status": "error", "message": "Invalid request method."}, status=405
    )
