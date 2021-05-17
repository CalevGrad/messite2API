import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from django.core.exceptions import ObjectDoesNotExist

from GradientServer import settings
from api.models import Event
from api.serializers import EventSerializer
from templates import bodys

from json import JSONDecodeError


class LongPollConsumer(AsyncHttpConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.post_group_name = None
        self.lpt = None
        self.old_events = False
        self.event_present = False

    async def handle(self, body):
        print(self.scope['user'], 'connected.')
        print(self.scope)
        print(body)

        # отсылаем 403, если пользователь не авторизован или токен истёк
        if self.scope['user'].is_anonymous:
            await self.send_response(403, json.dumps(bodys.token_error).encode('utf-8'), headers=[
                (b"Content-Type", b"application/json"),
            ])
            return

        # проверяем какие события клиент пропустил
        try:
            body_json = json.loads(body)
            client_event_id = int(body_json['event'])

            # если указанного event у пользователя нет, то возвращаем HTTP 400
            # соответственно event не будет также если events у пользователя нет вообще
            if not await self.check_event(self.scope['user'], client_event_id):
                await self.send_response(400, json.dumps(bodys.bad_request).encode('utf-8'), headers=[
                    (b"Content-Type", b"application/json"),
                ])
                return

            event = await self.get_first_event(self.scope['user'])

            self.event_present = True

            if event.id != client_event_id:
                self.old_events = True
                print('tut')
                events = await self.get_events(client_event_id)
                print(events)
                await self.send_response(200, json.dumps({
                    'type': 'old_events',
                    'event': event.id,
                    'data': events
                }).encode('utf-8'), headers=[
                    (b"Content-Type", b"application/json"),
                ])
                return

        except (JSONDecodeError, KeyError):
            pass

        self.post_group_name = 'user_{}'.format(self.scope['user'].id)  # задаём имя группы

        # отправляем хеадеры
        await self.send_headers(headers=[
            (b"Content-Type", b"application/json"),
        ])

        await self.channel_layer.group_add(self.post_group_name, self.channel_name)  # добавляем канал в группу

        # запускаем уничтожитель лонг пола
        self.lpt = asyncio.run_coroutine_threadsafe(self.long_polling_terminator(), asyncio.get_running_loop())

    @database_sync_to_async
    def get_first_event(self, user):
        """
        Получает последнее событие пользователя
        """
        return user.events.first()

    @database_sync_to_async
    def get_first_event_id(self, user):
        """
        Получает последнее событие пользователя
        """
        return user.events.first().id

    @database_sync_to_async
    def check_event(self, user, event_id):
        try:
            user.events.get(id=event_id)
            return True
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def get_events(self, event_id):
        events = Event.objects.filter(id__gt=event_id)
        return EventSerializer(events, many=True).data

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
        if self.lpt is not None:
            self.lpt.cancel()  # закрываем терминатор лонг полла
        if not self.old_events:
            await self.channel_layer.group_discard(
                self.post_group_name,
                self.channel_name,
            )

    async def new_message(self, event):
        print('Event NEW MESSAGE', event)
        await self.send_body(json.dumps(event).encode('utf-8'))

    async def new_dialog(self, event):
        print('Event NEW DIALOG', event)
        await self.send_body(json.dumps(event).encode('utf-8'))

    async def long_polling_terminator(self):
        """
        Ожидает LONG_POLLING_TIMEOUT секунд и завершает запрос клиента с ответом timeout
        """
        await asyncio.sleep(settings.LONG_POLLING_TIMEOUT)
        data = bodys.timeout
        if not self.event_present:
            data['event'] = await self.get_first_event_id(self.scope['user'])
        await self.send_body(json.dumps(data).encode('utf-8'))

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
