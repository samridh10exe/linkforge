import json
from datetime import timedelta
from unittest.mock import patch

from app.models.url import Url
from app.validators import utcnow


def test_redirect_returns_302_for_active_url(client, active_url):
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == active_url.original_url


def test_redirect_returns_404_for_unknown_code(client):
    response = client.get("/missing1", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_returns_410_for_inactive_url(client, active_url):
    Url.update(is_active=False).where(Url.id == active_url.id).execute()
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    payload = response.get_json()

    assert response.status_code == 410
    assert payload["error"]["message"] == "URL is no longer active"


def test_redirect_returns_410_for_expired_url(client, active_url):
    Url.update(expires_at=utcnow() - timedelta(minutes=5)).where(Url.id == active_url.id).execute()
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 410


def test_redirect_returns_miss_header_on_first_request(client, active_url):
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("X-Cache") == "MISS"


def test_redirect_returns_hit_header_from_cached_entry(client, active_url, monkeypatch):
    cached = json.dumps({
        "id": active_url.id,
        "user_id": active_url.user_id,
        "short_code": active_url.short_code,
        "original_url": active_url.original_url,
        "is_active": True,
        "expires_at": None,
    })
    monkeypatch.setattr("app.services.urls.cache_get", lambda key: cached)
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("X-Cache") == "HIT"
    assert response.headers["Location"] == active_url.original_url


def test_redirect_cache_hit_returns_410_for_inactive_cached_entry(client, active_url, monkeypatch):
    cached = json.dumps({
        "id": active_url.id,
        "user_id": active_url.user_id,
        "short_code": active_url.short_code,
        "original_url": active_url.original_url,
        "is_active": False,
        "expires_at": None,
    })
    monkeypatch.setattr("app.services.urls.cache_get", lambda key: cached)
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 410


def test_redirect_cache_hit_returns_410_for_expired_cached_entry(client, active_url, monkeypatch):
    cached = json.dumps({
        "id": active_url.id,
        "user_id": active_url.user_id,
        "short_code": active_url.short_code,
        "original_url": active_url.original_url,
        "is_active": True,
        "expires_at": (utcnow() - timedelta(hours=1)).isoformat(),
    })
    monkeypatch.setattr("app.services.urls.cache_get", lambda key: cached)
    response = client.get(f"/{active_url.short_code}", follow_redirects=False)
    assert response.status_code == 410
