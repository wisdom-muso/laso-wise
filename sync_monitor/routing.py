from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/sync_monitor/$', consumers.SyncStatusConsumer.as_asgi()),
]