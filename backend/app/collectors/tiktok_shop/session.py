"""Optional local authentication state; never inspect a user's existing browser profile."""
import json
import math
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
from http.cookiejar import Cookie
import httpx
from app.core.urls import TIKTOK_HOSTS
from app.collectors.tiktok_shop.exceptions import CollectorError

SESSION_FILE = Path(__file__).resolve().parents[3] / '.local' / 'tiktok-session.json'


class SessionStateError(CollectorError):
    pass


def sanitize_state(state: dict) -> dict:
    if not isinstance(state, dict) or not isinstance(state.get('cookies'), list):
        raise ValueError('Invalid session structure')
    cookies = []
    for cookie in state['cookies']:
        if not isinstance(cookie, dict):
            raise ValueError('Invalid cookie')
        domain = cookie.get('domain', '')
        if not isinstance(domain, str) or domain.lstrip('.') not in TIKTOK_HOSTS:
            continue
        expires = cookie.get('expires', -1)
        if not isinstance(expires, (int, float)) or not math.isfinite(expires):
            raise ValueError('Invalid expiry')
        if expires != -1 and expires <= time.time():
            continue
        if not all(isinstance(cookie.get(k), str) for k in ('name', 'value', 'path')):
            raise ValueError('Invalid cookie fields')
        if not cookie['path'].startswith('/'):
            raise ValueError('Invalid cookie path')
        cookies.append({k: cookie[k] for k in ('name', 'value', 'domain', 'path')} | {
            'expires': expires, 'secure': True,
            'httpOnly': bool(cookie.get('httpOnly', False)),
            'sameSite': cookie.get('sameSite') if cookie.get('sameSite') in ('Strict', 'Lax', 'None') else 'Lax'})
    origins = []
    for origin in state.get('origins', []):
        parts = urlsplit(origin.get('origin', ''))
        if (parts.scheme == 'https' and parts.hostname in TIKTOK_HOSTS and
                parts.port in (None, 443) and not parts.username and not parts.password):
            storage = origin.get('localStorage', [])
            if not isinstance(storage, list) or any(not isinstance(x, dict) or
                not all(isinstance(x.get(k), str) for k in ('name', 'value')) for x in storage):
                raise ValueError('Invalid local storage')
            origins.append({'origin': f'https://{parts.hostname}', 'localStorage': storage})
    return {'cookies': cookies, 'origins': origins}


def load_state(path: Path = None):
    path = path or SESSION_FILE
    if not path.exists():
        return None
    try:
        if path.stat().st_size > 2_000_000:
            raise ValueError('Session too large')
        return sanitize_state(json.loads(path.read_text(encoding='utf-8')))
    except (OSError, ValueError, TypeError, AttributeError):
        # Never include raw JSON, cookie values, or a parser exception in UI/logs.
        raise SessionStateError('Phiên TikTok đã lưu không hợp lệ. Chạy CONNECT_TIKTOK.bat để tạo lại phiên.') from None


def http_cookies(state) -> httpx.Cookies:
    jar = httpx.Cookies()
    for c in (state or {}).get('cookies', []):
        domain = c['domain']
        jar.jar.set_cookie(Cookie(0, c['name'], c['value'], None, False, domain,
            domain.startswith('.'), domain.startswith('.'), c['path'], True, True,
            int(c['expires']) if c['expires'] != -1 else None, c['expires'] == -1,
            None, None, {}, False))
    return jar


def session_status() -> str:
    try:
        state = load_state()
        return 'available' if state and (state['cookies'] or any(o['localStorage'] for o in state['origins'])) else 'missing'
    except SessionStateError:
        return 'invalid'


def save_state(state: dict, path: Path = None) -> None:
    path = path or SESSION_FILE
    clean = sanitize_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    try:
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(clean, handle)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
