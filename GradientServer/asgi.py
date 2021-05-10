import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.core.asgi import get_asgi_application
from starlette.middleware.cors import CORSMiddleware

from GradientServer.channelsmiddleware import TokenAuthMiddleware
from api.consumers import LongPollConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GradientServer.settings')

application = ProtocolTypeRouter({
    'http': URLRouter([
        url(r'api/longpoll/', TokenAuthMiddleware(
            LongPollConsumer.as_asgi()
        )),
        url(r'', get_asgi_application()),
    ]),
})

application = CORSMiddleware(application, allow_origins=['*'], allow_headers=['*'], allow_methods=['*'])
