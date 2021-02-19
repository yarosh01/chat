from django.urls import path
from chat.consumers import GroupChatConsumer, ChatConsumer

websocket_urls = [
    path('ws/groups/', GroupChatConsumer),
    path('ws/chat/<int:group_id>/', ChatConsumer),
]
