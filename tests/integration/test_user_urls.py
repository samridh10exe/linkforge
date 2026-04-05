from app.models.url import Url
from app.validators import utcnow


def test_get_urls_returns_user_scoped_rows(client, user):
    Url.create(
        user=user.id,
        short_code="abc123",
        original_url="https://example.com/a",
        title="A",
        is_active=True,
        expires_at=None,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    Url.create(
        user=user.id,
        short_code="def456",
        original_url="https://example.com/b",
        title="B",
        is_active=False,
        expires_at=None,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    response = client.get(f"/users/{user.id}/urls")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload) == 2
    assert {row["short_code"] for row in payload} == {"abc123", "def456"}


def test_get_urls_returns_404_for_missing_user(client):
    response = client.get("/users/9999/urls")
    assert response.status_code == 404
