#!/usr/bin/env python
"""
Generate a new Django SECRET_KEY for production use.
Run this script and copy the output to your environment variables.
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "="*70)
    print("🔐 NEW DJANGO SECRET KEY GENERATED")
    print("="*70)
    print(f"\n{secret_key}\n")
    print("="*70)
    print("\n📋 INSTRUCTIONS:")
    print("1. Copy the key above")
    print("2. Set it as environment variable on your server:")
    print("   export DJANGO_SECRET_KEY='<paste-key-here>'")
    print("\n⚠️  IMPORTANT: Keep this key secret! Don't commit it to Git.")
    print("="*70 + "\n")
