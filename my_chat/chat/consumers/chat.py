from channels.db import database_sync_to_async
from chat.models import ChatGroup, GroupParticipant, ChatMessage
from .base import BaseChatConsumer
from django.contrib.auth import get_user_model

class ChatConsumer(BaseChatConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_id = self.scope['kwargs']['group_id']
        self.group = None
        self.participants = []
        self.channel = f'group_{self.group_id}'
        
    async def connect(self):
        await super().connect()
        group = await self.get_group()
        if not group:
            await self._throw_error({'detail': 'Group not found'})
            await self.close()
            return
        participants = self.get_participants()
        if self.scope['user'].id not in participants:
            await self._throw_error({'detail': 'Access denied'})
            await self.close()
            return
        await self.channel_layer.group_add(self.channel, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.channel, self.channel_name)
        await super().disconnect(code=code)

    async def event_add_participants(self, event):
        user_id = event['data'].get('user_id')
        if not user_id:
            return self._throw_error({'detail': 'Missing user id'}, event=event['event'])
        participants = self.add_participants(user_id)
        return await self._send_message(participants, event=event['event'])

    async def event_send_message(self, event):
        message = event['data'].get('message')
        if not message:
            return self._throw_error({'detail': 'Missing message'}, event=event['event'])
        await self.save_message()
        return await self._group_send(event['data'])

    async def event_list_messages(self, event):
        messages = await self.get_messages()
        return await self._send_message(messages, event=event['event'])

    @database_sync_to_async
    def get_group(self):
        group = ChatGroup.objects.filte(pk=self.group_id).first()
        if group:
            self.group = group
        return group

    @database_sync_to_async
    def get_participants(self):
        participants = list(GroupParticipant.objects.filter(group=self.group).values_list('user', flat=True))
        self.participants = participants
        return participants

    @database_sync_to_async
    def add_participants(self, user_id):
        user = get_user_model().filter(pk=user_id).first()
        if user:
            participants, _ = GroupParticipant.objects.get_or_create(group=self.group, user=user)
        participants = self.get_participants()
        return participants

    @database_sync_to_async
    def save_message(self, message, user):
        m = ChatMessage(user=user, group=self.group, message=message)
        m.save()

    @database_sync_to_async
    def get_messages(self):
        messages = ChatMessage.objects.select_related('user').filter(group=self.group).order_by('id')
        res = []
        for message in messages:
            res.append({
                'id': message.id,
                'username': message.user.username,
                'message': message.message,
            })
        return res
