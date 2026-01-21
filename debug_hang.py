import os
import sys
import time


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()


log("Starting diagnostic script...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecodrop_project.settings")

try:
    log("Importing django...")
    import django

    log("Calling django.setup()...")
    django.setup()
    log("django.setup() completed.")

    log("Importing models from core...")
    from core.models import UserProfile

    log("UserProfile imported.")

    log("Diagnostic script finished successfully.")
except Exception as e:
    log(f"Error encountered: {e}")
    import traceback

    traceback.print_exc()
