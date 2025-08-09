import json
import urllib.parse
import jwt
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from authentication.models import User
from django.contrib.auth.models import AnonymousUser
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_user_by_payload

from .service import get_ai_response


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket connection"""
        # Debug auth info (properly indented inside method)
        user: User = self.scope.get('user')
        if not getattr(user, 'is_authenticated', False):
            # Try query string token fallback
            token = self._extract_token_from_query()
            if token:
                resolved = await self._resolve_user(token)
                if resolved:
                    self.scope['user'] = resolved
                    user = resolved
        print(
            f"[WS CONNECT] user={getattr(user, 'id', None)} is_authenticated={getattr(user, 'is_authenticated', False)}"
        )
        await self.accept()
        # Add to user-specific channel group for multi-tab sync
        if getattr(user, 'is_authenticated', False):
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            # Send last N messages history
            history = await self._get_recent_messages(user, limit=20)
            await self.send(json.dumps({
                'type': 'history',
                'messages': [
                    {
                        'id': str(m.id),
                        'content': m.content,
                        'sender': getattr(m.sender, 'username', 'unknown'),
                        'timestamp': m.timestamp.isoformat(),
                    } for m in history
                ]
            }))
        await self.send(json.dumps({"info": "Connected"}))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"WebSocket disconnected with code: {close_code}")
        user: User = self.scope.get('user')
        if getattr(user, 'is_authenticated', False) and hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        user = self.scope.get('user')
        try:
            text_data_json = json.loads(text_data)
            # If not authenticated yet, allow first auth message with token
            if not getattr(user, 'is_authenticated', False):
                # 1. Try token inside message payload
                token = text_data_json.get('token')
                # 2. Fallback to query param token
                if not token:
                    token = self._extract_token_from_query()
                if token:
                    resolved, status = await self._resolve_user(token)
                    if resolved:
                        self.scope['user'] = resolved
                        user = resolved
                        await self.send(json.dumps({'info': 'Authenticated', 'code': 'AUTH_OK'}))
                        if 'message' not in text_data_json:
                            return  # stop if only auth payload
                    else:
                        code = 'TOKEN_EXPIRED' if status == 'Token expired' else 'TOKEN_ERROR'
                        await self.send(json.dumps({'error': status or 'Invalid token', 'code': code}))
                        return
                else:
                    await self.send(json.dumps({'error': 'Not authenticated', 'hint': 'Send {"token": "<JWT>"} or append ?token=... to URL'}))
                    return
            message = text_data_json.get('message', '')
            
            print(f"Received message: {message}")

            print("Processing message...")

            sender: User = user  # already validated

            # Get AI response (persisted)
            response = await get_ai_response(user=sender, user_message=message)

            # Broadcast user message then AI response to group (re-fetch persisted messages not necessary here)
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'chat.message',
                    'payload': {
                        'kind': 'user',
                        'content': message,
                    }
                })
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'chat.message',
                    'payload': {
                        'kind': 'bot',
                        'content': response,
                    }
                })
            else:
                # Fallback directly to sender
                await self.send(text_data=json.dumps({'response': response}))
            
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

    def _extract_token_from_query(self) -> str | None:
        raw_qs = self.scope.get('query_string', b'').decode()
        if not raw_qs:
            return None
        params = urllib.parse.parse_qs(raw_qs)
        if 'token' in params:
            return params['token'][0]
        if 'Authorization' in params:
            val = params['Authorization'][0]
            if val.startswith('JWT '):
                return val.split(' ', 1)[1]
        return None

    async def _resolve_user(self, token: str) -> tuple[User | None, str | None]:
        """Attempt to resolve and return (user, error_message).

        Returns (user, None) on success, (None, reason) on failure.
        """
        try:
            payload = jwt.decode(
                token,
                jwt_settings.JWT_SECRET_KEY,
                algorithms=[jwt_settings.JWT_ALGORITHM],
                options={"verify_exp": True},
            )
            # get_user_by_payload performs DB access (sync); wrap it
            user = await sync_to_async(get_user_by_payload)(payload)
            if user and user.is_active:
                return user, None
            return None, "Inactive or missing user"
        except jwt.ExpiredSignatureError:
            return None, "Token expired"
        except jwt.InvalidTokenError as e:  # includes DecodeError, InvalidSignatureError
            return None, f"Invalid token: {e}" 
        except Exception as e:  # pragma: no cover
            print(f"[WS AUTH] Token decode failed: {e}")
            return None, "Token decode failure"

    async def chat_message(self, event):  # type: ignore
        payload = event.get('payload', {})
        await self.send(json.dumps({'type': 'message', **payload}))

    @database_sync_to_async
    def _get_recent_messages(self, user: User, limit: int = 20):
        from chat.models import Message, Conversation
        # Latest active conversation
        conv = Conversation.objects.filter(user=user, is_active=True).order_by('-updated_at').first()
        if not conv:
            return []
        return list(Message.objects.filter(conversation=conv).order_by('-timestamp')[:limit][::-1])
