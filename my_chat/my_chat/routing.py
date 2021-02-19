from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urls
from channels.sessions import SessionMiddlewareStack
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urls,
        )
    )
})

