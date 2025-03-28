import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PostgresNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("LRCW", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("LRCW", self.channel_name)

    async def postgres_notify(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({"message": message}))
