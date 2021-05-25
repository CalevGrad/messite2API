import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.core.asgi import get_asgi_application
from starlette.middleware.cors import CORSMiddleware

from GradientServer import settings
from GradientServer.channelsmiddleware import TokenAuthMiddleware
from api.consumers import LongPollConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GradientServer.settings')

application = ProtocolTypeRouter({
    'http': URLRouter([
        url(r'api/longpoll/', CORSMiddleware(TokenAuthMiddleware(
            LongPollConsumer.as_asgi()
        ), allow_origins=settings.CORS_ALLOWED_ORIGINS, allow_headers=['*'], allow_methods=['*'])),
        url(r'', get_asgi_application()),
    ]),
})

