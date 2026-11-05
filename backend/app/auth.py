"""Experimental shared-password access for a single household."""
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import deque
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse

COOKIE = 'tablet_agent_session'
SESSION_SECONDS = 7 * 24 * 60 * 60


class AccessControl:
    def __init__(self):
        self.password = os.environ.get('AUTH_PASSWORD', '')
        self.enabled = bool(self.password)
        secret = os.environ.get('AUTH_SESSION_SECRET', '')
        if self.enabled and len(secret.encode('utf-8')) < 32:
            raise RuntimeError('AUTH_SESSION_SECRET must be at least 32 bytes when AUTH_PASSWORD is set')
        self.key = hmac.new(secret.encode('utf-8'), self.password.encode('utf-8'), hashlib.sha256).digest()
        self.secure = os.environ.get('AUTH_COOKIE_SECURE', 'true').lower() == 'true'
        self.failures = deque()
        self.lock = threading.Lock()

    def authenticated(self, request):
        if not self.enabled:
            return True
        token = request.cookies.get(COOKIE, '')
        try:
            expiry, nonce, signature = token.split('.')
            payload = expiry + '.' + nonce
            expected = hmac.new(self.key, payload.encode('ascii'), hashlib.sha256).hexdigest()
            return int(expiry) > int(time.time()) and hmac.compare_digest(signature, expected)
        except (ValueError, UnicodeError):
            return False

    def token(self):
        payload = str(int(time.time()) + SESSION_SECONDS) + '.' + secrets.token_hex(16)
        signature = hmac.new(self.key, payload.encode('ascii'), hashlib.sha256).hexdigest()
        return payload + '.' + signature

    def check_password(self, candidate):
        now = time.monotonic()
        with self.lock:
            while self.failures and self.failures[0] <= now - 60:
                self.failures.popleft()
            if len(self.failures) >= 8:
                return 'limited'
            if isinstance(candidate, str) and hmac.compare_digest(candidate.encode('utf-8'), self.password.encode('utf-8')):
                self.failures.clear()
                return 'ok'
            self.failures.append(now)
            return 'invalid'

    @staticmethod
    def valid_origin(request):
        origin = request.headers.get('origin')
        if not origin:
            return True
        try:
            parsed = urlsplit(origin)
            return parsed.scheme in ('http', 'https') and parsed.netloc.lower() == request.headers.get('host', '').lower()
        except ValueError:
            return False


def install_auth(app):
    auth = AccessControl()

    @app.middleware('http')
    async def protect_api(request: Request, call_next):
        path = request.url.path
        if auth.enabled and path.startswith('/api/'):
            if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                if not auth.valid_origin(request):
                    return JSONResponse({'error': 'Origine non consentita.'}, status_code=403)
                if request.method in ('POST', 'PUT', 'PATCH') and not request.headers.get('content-type', '').lower().startswith('application/json'):
                    return JSONResponse({'error': 'Formato non valido.'}, status_code=415)
            if path not in ('/api/health', '/api/auth/login', '/api/auth/status') and not auth.authenticated(request):
                return JSONResponse({'error': 'Accesso richiesto.'}, status_code=401)
        return await call_next(request)

    @app.get('/api/auth/status')
    def auth_status(request: Request):
        return {'enabled': auth.enabled, 'authenticated': auth.authenticated(request)}

    @app.post('/api/auth/login')
    async def login(request: Request):
        if not auth.enabled:
            return JSONResponse({'error': 'Accesso non configurato.'}, status_code=404)
        try:
            data = await request.json()
        except ValueError:
            data = {}
        candidate = data.get('password') if isinstance(data, dict) else None
        result = auth.check_password(candidate)
        if result == 'limited':
            return JSONResponse({'error': 'Troppi tentativi. Riprova tra un minuto.'}, status_code=429)
        if result != 'ok':
            return JSONResponse({'error': 'Password non corretta.'}, status_code=401)
        response = JSONResponse({'ok': True}, headers={'Cache-Control': 'no-store'})
        response.set_cookie(COOKIE, auth.token(), max_age=SESSION_SECONDS, httponly=True, secure=auth.secure, samesite='lax', path='/')
        return response

    @app.post('/api/auth/logout')
    def logout():
        response = JSONResponse({'ok': True}, headers={'Cache-Control': 'no-store'})
        response.delete_cookie(COOKIE, path='/', secure=auth.secure, httponly=True, samesite='lax')
        return response
