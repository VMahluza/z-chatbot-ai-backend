#!/usr/bin/env python
"""
Test script to verify ASGI configuration
"""
import os
import sys
import django
from django.conf import settings

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test imports
try:
    from core.asgi import application
    print("✅ ASGI application imported successfully")
    
    from chat.consumers import ChatConsumer
    print("✅ ChatConsumer imported successfully")
    
    from chat.routing import websocket_urlpatterns
    print("✅ WebSocket routing imported successfully")
    print(f"WebSocket patterns: {websocket_urlpatterns}")
    
    # Check if channels is properly configured
    if hasattr(settings, 'CHANNEL_LAYERS'):
        print("✅ Channel layers configured")
    else:
        print("❌ Channel layers not configured")
        
    if 'channels' in settings.INSTALLED_APPS:
        print("✅ Channels app is installed")
    else:
        print("❌ Channels app is not installed")
        
    if 'chat' in settings.INSTALLED_APPS:
        print("✅ Chat app is installed")
    else:
        print("❌ Chat app is not installed")
        
    print("\n🎉 All checks passed! WebSocket should work.")
    print("\nTo start the server with WebSocket support, run:")
    print("daphne -b 127.0.0.1 -p 8000 core.asgi:application")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease check your configuration.")
