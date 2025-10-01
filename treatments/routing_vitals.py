"""
WebSocket routing for vital signs
"""
from django.urls import re_path
from . import consumers_vitals

websocket_urlpatterns = [
    re_path(r'ws/vitals/$', consumers_vitals.VitalsConsumer.as_asgi()),
    re_path(r'ws/vitals/alerts/$', consumers_vitals.VitalsAlertsConsumer.as_asgi()),
]