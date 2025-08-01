import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        print("WebSocket connection established")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            print(f"Received message: {message}")
            
            # Simple echo response for now - you can integrate with AI here
            response = f"Echo: {message}"
            
            # Send response back to WebSocket
            await self.send(text_data=json.dumps({
                'response': response
            }))
            
        except json.JSONDecodeError:
            # Handle invalid JSON
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            # Handle other errors
            print(f"Error in ChatConsumer: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Internal server error'
            }))
