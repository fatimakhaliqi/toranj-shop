from django.conf import settings
from django.core.cache import cache

from config.ratelimit import client_ip


def _key(request, username):
    return f"login-fail:{client_ip(request)}:{(username or '').strip().lower()}"


def is_locked(request, username):
    return cache.get(_key(request, username), 0) >= settings.LOGIN_MAX_ATTEMPTS


def register_failure(request, username):
    key = _key(request, username)
    cache.set(key, cache.get(key, 0) + 1, settings.LOGIN_LOCKOUT_SECONDS)


def reset(request, username):
    cache.delete(_key(request, username))
