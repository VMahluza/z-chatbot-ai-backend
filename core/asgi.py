"""
ASGI config for core project.
It exposes the ASGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
websocket_urlpatterns = []
try:
    from chat.routing import websocket_urlpatterns as _ws_patterns  # type: ignore
    websocket_urlpatterns = _ws_patterns
except Exception as e:  # pragma: no cover
    # Avoid crashing ASGI import due to a syntax/runtime error in consumer; will log and continue.
    print(f"[ASGI WARNING] Failed to import chat.routing: {e}")

try:
    from core.channels.jwt_auth import JWTAuthMiddlewareStack
except Exception as e:  # pragma: no cover
    print(f"[ASGI WARNING] Failed to import JWTAuthMiddlewareStack: {e}")
    def JWTAuthMiddlewareStack(inner):  # fallback no-op
        return inner

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

print("ASGI application initialized (websocket patterns loaded:", len(websocket_urlpatterns), ")")

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)