"""Script to rename all student_id references to school_id"""
import os
from pathlib import Path

# Files to update
files_to_update = [
    'core/views.py',
    'core/admin.py',
    'core/forms.py',
    'core/management/commands/create_test_user.py',
    'core/management/commands/fix_qr_codes.py',
    'core/management/commands/fix_user_types.py',
    'fix_user_types.py',
]

# HTML templates
templates = [
    'templates/core/admin_user_edit.html',
    'templates/core/admin_user_add.html',
    'templates/core/register.html',
    'templates/core/admin_transactions.html',
    'templates/core/debug_qr_codes.html',
    'templates/core/teacher_profile.html',
    'templates/core/student_profile.html',
]

all_files = files_to_update + templates

base_path = Path(__file__).parent

for file_path in all_files:
    full_path = base_path / file_path
    if full_path.exists():
        try:
            content = full_path.read_text(encoding='utf-8')
            updated_content = content.replace('student_id', 'school_id')
            full_path.write_text(updated_content, encoding='utf-8')
            print(f"✓ Updated: {file_path}")
        except Exception as e:
            print(f"✗ Error updating {file_path}: {e}")
    else:
        print(f"⚠ File not found: {file_path}")

print("\n✅ Renaming complete!")
