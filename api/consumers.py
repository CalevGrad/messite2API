import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from api.models import Dialog, Message
from api.serializers import MessageSerializer, DialogSerializer


class UserConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        userId = self.scope['user'].id
        self.post_group_name = 'user{}'.format(userId)
        await self.channel_layer.group_add(
            self.post_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.post_group_name,
            self.channel_name,
        )

    async def receive_json(self, content, **kwargs):
        content_type = content['type']

        if content_type == 'dialog':
            first_message = content['first_message']
            owners = content['owners']
            new_dialog = await self.create_new_dialogs(first_message, owners)
            data = DialogSerializer(new_dialog)
            await self.channel_layer.group_send(
                'type': 'new_dialog',
            'dialog': data
            )
            elif content_type == 'message':
            dialog_id = content['dialog']
            text_message = content['text']
            new_message = await self.create_new_message(dialog_id, text_message)
            data = MessageSerializer(new_message).data
            await self.channel_layer.group_send(
                'type': 'new_message',
            'message': data
            )

        async def new_comment(self, event):
            message = event['message']
            await self.send_json(
                'message': message,
            )

            async def new_dialog(self, event):
                dialog = event['dialog']
                await self.send_json(
                    'dialog': dialog,
                )

                async def create_new_message(self, dialog_id, text_message):
                    pass

                async def create_new_dialog(self, first_message, owners):
                    pass
