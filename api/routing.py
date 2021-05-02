from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'userws/$', consumers.UserConsumer.as_asgi()),
]