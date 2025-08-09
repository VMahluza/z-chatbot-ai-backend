import json
import urllib.parse
import jwt
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
        await self.send(json.dumps({"info": "Connected"}))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"WebSocket disconnected with code: {close_code}")

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

            # Get AI response
            response = await get_ai_response(user_message= message, user=sender)

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
