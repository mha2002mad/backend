from django.urls import re_path
from consumers import PostgresNotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', PostgresNotificationConsumer.as_asgi()),
]
