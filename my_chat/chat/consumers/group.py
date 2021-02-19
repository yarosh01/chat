from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat.models import GroupParticipant, ChatGroup
from .base import BaseChatConsumer


class GroupChatConsumer(BaseChatConsumer):

    async def event_group_list(self, event):
        data = await self.group_list(self.scope['user'])
        await self._send_message(data, event=event['event'])

    # возможно я затупил и надо убрать await в data
    async def event_user_list(self, event):
        data = await self.user_list(self.scope['user'])
        await self._send_message(data, event=event['event'])

    # возможно я затупил и надо убрать await в data
    async def event_group_create(self, event):
        name = event['data'].get('name')
        if not name:
            return await self._throw_error({'detail': 'Missing group name'}, event=event['event'])
        data = await self.group_create(name, self.scope['user'])
        await self._send_message(data, event=event['event'])

    @database_sync_to_async
    def group_list(self, user):
        group_ids = list(GroupParticipant.objects.filter(user=user).values_list('group', flat=True))
        res = []
        for g in ChatGroup.objects.filter(id__in=group_ids):
            res.append({
                'id': g.id,
                'name': g.name,
                'link': g.link,
            })
        return res

    @database_sync_to_async
    def user_list(self, user):
        users = get_user_model().objects.all().exclude(pk=user.id)
        res = []
        for u in users:
            res.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
            })
        return res

    @database_sync_to_async
    def group_create(self, name, user):
        group = ChatGroup(name=name)
        group.save()
        participant = GroupParticipant(user=user, group=group)
        participant.save()
        return {'id': group.id, 'name': group.name, 'link': group.link}