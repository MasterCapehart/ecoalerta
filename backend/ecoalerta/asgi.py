"""
ASGI config for ecoalerta project.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecoalerta.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from reportes import routing

# Django ASGI app para HTTP (sin timeout de Channels)
django_asgi_app = get_asgi_application()


class TimeoutFreeRouter:
    """
    Router que usa Django puro para HTTP (sin timeout de Channels)
    y Channels solo para WebSocket.
    """
    def __init__(self):
        self.channels_app = ProtocolTypeRouter({
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(
                URLRouter(routing.websocket_urlpatterns)
            ),
        })

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            await self.channels_app(scope, receive, send)
        else:
            # HTTP va directo a Django sin pasar por Channels
            await django_asgi_app(scope, receive, send)


application = TimeoutFreeRouter()

