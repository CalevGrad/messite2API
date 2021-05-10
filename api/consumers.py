import asyncio
import json

from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.http import AsyncHttpConsumer

from templates import bodys

from json import JSONDecodeError


class LongPollConsumer(AsyncHttpConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.post_group_name = None

    async def handle(self, body):
        print(self.scope['user'])
        print(body)

        if self.scope['user'].is_anonymous:
            await self.send_response(403, json.dumps(bodys.token_error).encode('utf-8'), headers=[
                (b"Content-Type", b"application/json"),
            ])
            return

        self.post_group_name = 'user_{}'.format(self.scope['user'].id)

        await self.send_headers(headers=[
            (b"Content-Type", b"application/json"),
        ])

        await self.channel_layer.group_add(self.post_group_name, self.channel_name)

    async def http_request(self, message):
        """
        Async entrypoint - concatenates body fragments and hands off control
        to ``self.handle`` when the body has been completely received.
        """
        if "body" in message:
            self.body.append(message["body"])
        if not message.get("more_body"):
            try:
                await self.handle(b"".join(self.body))
            finally:
                pass
                # await self.disconnect()
                # raise StopConsumer()

    async def disconnect(self):
        # await self.send_body(json.dumps({"detail": "Connection timeout", "code": "timeout"}).encode('utf-8'))
        await self.channel_layer.group_discard(
            self.post_group_name,
            self.channel_name,
        )

    async def new_message(self, event):
        print('Event NEW MESSAGE', event)
        await self.send_body(json.dumps(event).encode(('utf-8')))

    async def new_dialog(self, event):
        print('Event NEW DIALOG', event)
        await self.send_body(json.dumps(event).encode(('utf-8')))


# class UserConsumer(AsyncJsonWebsocketConsumer):
#     async def connect(self):
#         print(self.scope['user'], ' connect')
#
#         if self.scope['user'].is_anonymous:
#             print('close connect')
#             await self.close(403)
#         else:
#             print('connect success')
#
#         user_id = self.scope['user'].id
#         self.post_group_name = 'user{}'.format(user_id)
#
#         await self.channel_layer.group_add(
#             self.post_group_name,
#             self.channel_name,
#         )
#         await self.accept()
#
#     async def disconnect(self, code):
#         await self.channel_layer.group_discard(
#             self.post_group_name,
#             self.channel_name,
#         )
#
#     async def receive_json(self, content, **kwargs):
#         print('receive_json', content, self.scope)
#
#         content_type = content['type']
#
#         if content_type == 'dialog':
#             first_message = content['first_message']
#             owners = content['owners']
#             new_dialog = await self.create_new_dialog(first_message, owners)
#             data = DialogSerializer(new_dialog)
#             await self.channel_layer.group_send(
#                 self.post_group_name,
#                 {
#                     'type': 'new_dialog',
#                     'dialog': data
#                 },
#             )
#         elif content_type == 'message':
#             dialog_id = content['dialog']
#             text_message = content['text']
#             print('new message', dialog_id, text_message)
#             new_message = await self.create_new_message(dialog_id, text_message)
#             data = MessageSerializer(new_message).data
#             await self.channel_layer.group_send(
#                 self.post_group_name,
#                 {
#                     'type': 'new_message',
#                     'message': data,
#                 }
#             )
#
#     async def new_message(self, event):
#         message = event['message']
#         await self.send_json(
#             {
#                 'message': message,
#             }
#         )
#
#     async def new_dialog(self, event):
#         dialog = event['dialog']
#         await self.send_json(
#             {
#                 'dialog': dialog,
#             }
#         )
#
#     @database_sync_to_async
#     def create_new_message(self, dialog_id, text_message):
#         return None
#
#     @database_sync_to_async
#     def create_new_dialog(self, first_message, owners):
#         return None
