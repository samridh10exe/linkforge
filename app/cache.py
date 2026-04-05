import redis as redis_lib
from flask import current_app

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
        _pool = redis_lib.ConnectionPool.from_url(url, decode_responses=True)
    return _pool


def _client():
    return redis_lib.Redis(connection_pool=_get_pool())


def cache_get(key):
    try:
        return _client().get(key)
    except Exception:
        return None


def cache_set(key, value, ttl=300):
    try:
        _client().set(key, value, ex=ttl)
    except Exception:
        pass


def cache_delete(key):
    try:
        _client().delete(key)
    except Exception:
        pass
