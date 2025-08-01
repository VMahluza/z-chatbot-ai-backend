#!/usr/bin/env python
"""
Script to test if runserver will use ASGI
"""
import os
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print("Django Settings Check:")
print(f"- ASGI_APPLICATION: {getattr(settings, 'ASGI_APPLICATION', 'Not set')}")
print(f"- INSTALLED_APPS contains 'daphne': {'daphne' in settings.INSTALLED_APPS}")
print(f"- INSTALLED_APPS contains 'channels': {'channels' in settings.INSTALLED_APPS}")

# Check if daphne is available for runserver
try:
    from django.core.management.commands.runserver import Command as RunServerCommand
    print(f"- Django runserver command available: Yes")
    
    # Check if daphne integration is working
    if hasattr(settings, 'ASGI_APPLICATION') and settings.ASGI_APPLICATION:
        print("✅ Django should use ASGI with runserver")
        print("\nTo start your server with WebSocket support, run:")
        print("python manage.py runserver")
    else:
        print("❌ ASGI not properly configured")
        
except ImportError as e:
    print(f"❌ Error importing runserver: {e}")

print("\nTesting ASGI application import...")
try:
    from core.asgi import application
    print("✅ ASGI application imports successfully")
except Exception as e:
    print(f"❌ ASGI application import error: {e}")
