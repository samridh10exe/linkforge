from datetime import timedelta

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
