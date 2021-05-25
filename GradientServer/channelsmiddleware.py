from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import User, AnonymousUser
from django.db import close_old_connections
from django.http import parse_cookie
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack

from django.urls import resolve


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom token auth middleware
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # close_old_connections()

        token = ''

        for name, value in scope.get("headers", []):
            if name == b"authorization":
                try:
                    token = value.decode("latin1").split()[1]
                except IndexError:
                    token = ''
                break

        # token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]

        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            print(e)
            scope['user'] = AnonymousUser()
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope['user'] = await self.get_user(decoded_data)
            # print('middl', scope['user'])

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, data):
        try:
            user = get_user_model().objects.get(id=data["user_id"])
            return user
        except User.DoesNotExist:
            return AnonymousUser()
