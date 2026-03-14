import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ReporteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join groups
        await self.channel_layer.group_add("reportes_general", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave groups
        await self.channel_layer.group_discard("reportes_general", self.channel_name)

    # Receive message from WebSocket (not used for this one-way notification system yet)
    async def receive(self, text_data):
        pass

    # Handler for 'reporte_creado' type messages
    async def reporte_creado(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'reporte_creado',
            'data': event['data']
        }))

    # Handler for 'reporte_actualizado' type messages
    async def reporte_actualizado(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reporte_actualizado',
            'data': event['data']
        }))
