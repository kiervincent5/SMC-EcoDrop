import uuid
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from .models import UserProfile, Device


def get_next_available_ids():
    """Generate the next available student and faculty IDs for display in forms"""
    current_year_short = str(datetime.now().year)[2:]  # "25" for 2025
    current_year_full = str(datetime.now().year)  # "2025"

    # Get next student ID (Format: C25-0001)
    last_student = (
        UserProfile.objects.filter(school_id__startswith=f"C{current_year_short}-")
        .order_by("-school_id")
        .first()
    )

    if last_student and last_student.school_id:
        try:
            last_num = int(last_student.school_id.split("-")[1])
            next_school_id = f"C{current_year_short}-{str(last_num + 1).zfill(4)}"
        except:
            next_school_id = f"C{current_year_short}-0001"
    else:
        next_school_id = f"C{current_year_short}-0001"

    # Get next faculty ID (Format: SMCIC-001-2025)
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
                next_faculty_id = (
                    f"SMCIC-{str(last_num + 1).zfill(3)}-{current_year_full}"
                )
            else:
                next_faculty_id = f"SMCIC-001-{current_year_full}"
        except:
            next_faculty_id = f"SMCIC-001-{current_year_full}"
    else:
        next_faculty_id = f"SMCIC-001-{current_year_full}"

    return next_school_id, next_faculty_id


def authenticate_device(request):
    """Helper function to authenticate device API requests via Bearer token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    api_key = auth_header.split(" ")[1]
    try:
        return Device.objects.get(api_key=api_key)
    except Device.DoesNotExist:
        return None


def generate_barcode_buffer(school_id, include_text=True):
    """Generate a barcode image buffer for a given student ID"""
    # Remove hyphens for barcode standard compatibility
    barcode_data = school_id.replace("-", "")

    try:
        code128 = barcode.get_barcode_class("code128")
        # writer=ImageWriter() ensures we get a PNG/Image
        barcode_instance = code128(barcode_data, writer=ImageWriter())

        buffer = BytesIO()
        options = {
            "module_width": 0.3,
            "module_height": 15.0 if include_text else 10.0,
            "quiet_zone": 6.5 if include_text else 3.0,
            "font_size": 12 if include_text else 0,
            "text_distance": 5.0,
            "write_text": include_text,
        }
        barcode_instance.write(buffer, options=options)
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise Exception(f"Barcode generation failed: {str(e)}")


def generate_id_card_image(user):
    """Generate an ID card image buffer (1012x638) with user info and barcode"""
    profile = user.profile
    school_id = profile.school_id or "NO-ID"

    # Dimensions for standard ID card aspect ratio
    width, height = 1012, 638
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)

    # Styling: Blue Header Section
    draw.rectangle([(0, 0), (width, 150)], fill="#1e40af")

    # Load fonts (fallback to default if arial is missing)
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        name_font = ImageFont.truetype("arial.ttf", 50)
        info_font = ImageFont.truetype("arial.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    # Draw School Info
    draw.text(
        (width // 2, 50),
        "St. Michael's College",
        fill="white",
        font=title_font,
        anchor="mm",
    )
    draw.text(
        (width // 2, 100), "Iligan City", fill="white", font=info_font, anchor="mm"
    )

    # Draw User Name
    full_name = f"{user.first_name} {user.last_name}".upper() or user.username.upper()
    draw.text((width // 2, 250), full_name, fill="#1e40af", font=name_font, anchor="mm")

    # Draw ID Label
    draw.text(
        (width // 2, 320), f"ID: {school_id}", fill="black", font=info_font, anchor="mm"
    )

    # Generate and past Barcode (without text as we manually draw ID above)
    barcode_buffer = generate_barcode_buffer(school_id, include_text=False)
    barcode_img = Image.open(barcode_buffer)
    # Resize barcode to fit nicely on the card
    barcode_img = barcode_img.resize((600, 120))
    card.paste(barcode_img, ((width - 600) // 2, 400))

    # Save final result to image buffer
    response_buffer = BytesIO()
    card.save(response_buffer, format="PNG")
    response_buffer.seek(0)
    return response_buffer
