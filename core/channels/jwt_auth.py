"""Custom JWT Auth middleware for Channels to populate scope['user'] using graphql-jwt tokens.

Adds support for tokens passed as:
- Query string: ?token=... OR ?Authorization=JWT <token>
- WebSocket subprotocol 'auth.token'
- Header during WebSocket handshake (if ASGI server exposes headers): Authorization: JWT <token>
- Cookie 'jwt' (optional)
"""
from __future__ import annotations
import urllib.parse
from typing import Callable, Awaitable
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from graphql_jwt.settings import jwt_settings
from graphql_jwt.utils import get_authorization_header
from graphql_jwt.shortcuts import get_user_by_payload
import jwt

User = get_user_model()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        # Ensure DB connections are usable
        close_old_connections()
        token = self._extract_token()
        if token:
            user = await self._get_user(token)
            if user:
                self.scope['user'] = user
        inner = self.inner(self.scope)
        return await inner(receive, send)

    def _extract_token(self) -> str | None:
        # 1. Query string
        query_string = self.scope.get('query_string', b'').decode()
        if query_string:
            params = urllib.parse.parse_qs(query_string)
            if 'token' in params:
                return params['token'][0]
            if 'Authorization' in params:
                auth_val = params['Authorization'][0]
                if auth_val.startswith('JWT '):
                    return auth_val.split(' ', 1)[1]
        # 2. Headers
        cookie_header = None
        for name, value in self.scope.get('headers', []):
            if name == b'authorization':
                header_val = value.decode()
                if header_val.startswith('JWT '):
                    return header_val.split(' ', 1)[1]
            if name == b'cookie':
                cookie_header = value.decode()
        # 2b. Parse cookie header manually (Channels does not always populate scope['cookies'])
        if cookie_header:
            cookies = {}
            for part in cookie_header.split(';'):
                if '=' in part:
                    k, v = part.split('=', 1)
                    cookies[k.strip()] = v.strip()
            for key in ('token', 'auth_token', 'jwt'):
                if key in cookies:
                    return cookies[key]
        # 3. Cookies
        cookies = self.scope.get('cookies') or {}
        if isinstance(cookies, dict) and 'jwt' in cookies:
            return cookies['jwt']
        # 4. Subprotocol (rare)
        subprotocols = self.scope.get('subprotocols', []) or []
        for sp in subprotocols:
            if sp.startswith('auth.token.'):  # auth.token.<JWT>
                return sp.split('.', 2)[2]
        return None

    async def _get_user(self, token: str):
        try:
            payload = jwt.decode(token, jwt_settings.JWT_SECRET_KEY, algorithms=[jwt_settings.JWT_ALGORITHM])
            user = get_user_by_payload(payload)
            return user
        except Exception:
            return None


def JWTAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack
    # Wrap default stack so session & auth run first (so AnonymousUser default is set)
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
