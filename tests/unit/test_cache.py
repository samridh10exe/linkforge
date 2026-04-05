import json
from unittest.mock import patch

from flask import Flask

import app.cache as cache_module
from app.cache import cache_delete, cache_get, cache_set


def test_cache_get_returns_none_when_redis_is_down():
    app = Flask(__name__)
    app.config["REDIS_URL"] = "redis://localhost:1/0"
    cache_module._pool = None
    with app.app_context():
        assert cache_get("nonexistent") is None


def test_cache_set_silently_fails_when_redis_is_down():
    app = Flask(__name__)
    app.config["REDIS_URL"] = "redis://localhost:1/0"
    cache_module._pool = None
    with app.app_context():
        cache_set("key", "value")


def test_cache_delete_silently_fails_when_redis_is_down():
    app = Flask(__name__)
    app.config["REDIS_URL"] = "redis://localhost:1/0"
    cache_module._pool = None
    with app.app_context():
        cache_delete("key")


def test_cache_roundtrip_when_redis_is_available(monkeypatch):
    store = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def set(self, key, value, ex=None):
            store[key] = value

        def delete(self, key):
            store.pop(key, None)

    monkeypatch.setattr(cache_module, "_client", lambda: FakeRedis())

    app = Flask(__name__)
    with app.app_context():
        assert cache_get("k") is None
        cache_set("k", "v")
        assert cache_get("k") == "v"
        cache_delete("k")
        assert cache_get("k") is None
