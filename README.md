# EcoDrop - Bottle Recycling Rewards System

A Django web application for managing bottle recycling rewards with IoT integration.

## Features

- **User Authentication**: Login/logout system
- **Points System**: Users earn points for recycling bottles
- **Rewards Catalog**: Redeem points for various rewards
- **Admin Dashboard**: Manage users, rewards, and transactions
- **IoT API**: REST endpoint for EcoDrop machines to record deposits
- **QR Code Integration**: Each user has a unique QR code for machine identification

## Project Structure

```
ecodrop_project/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── ecodrop_project/         # Main project settings
│   ├── __init__.py
│   ├── settings.py          # Django configuration
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── core/                    # Main application
│   ├── __init__.py
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # App URL routing
│   ├── forms.py             # Django forms
│   ├── admin.py             # Admin interface
│   ├── apps.py              # App configuration
│   ├── tests.py             # Unit tests
│   └── migrations/          # Database migrations
└── templates/               # HTML templates
    ├── base.html            # Base template
    └── core/
        ├── login.html       # Login page
        ├── dashboard.html   # User dashboard
        ├── rewards.html     # Rewards catalog
        └── admin_dashboard.html # Admin panel
```

## Setup Instructions

1. **Install Python** (3.8 or higher)
2. **Install Django**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Main app: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Database Models

- **UserProfile**: Extends Django User with points and QR code data
- **Entry**: Records bottle deposit transactions
- **RewardItem**: Available rewards in the catalog
- **RedeemedPoints**: Tracks reward redemptions

## API Endpoints

### IoT Device Endpoint
```
POST /api/deposit/
Content-Type: application/json

{
    "user_id": "SMC-USER-student123",
    "bottles": 3
}
```

**Response:**
```json
{
    "status": "success",
    "message": "30 points added."
}
```

## Usage

1. **For Students**: Login with your credentials to view points and redeem rewards
2. **For Admins**: Access admin dashboard to manage the system
3. **For IoT Devices**: Use the API endpoint to record bottle deposits

## Points System

- **10 points** per bottle deposited
- Points are automatically added when bottles are deposited via IoT machines
- Points can be redeemed for various rewards in the catalog
