from app.models import Event, Url


def test_post_shorten_creates_url_and_event(client, user):
    response = client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/new",
            "title": "New url",
            "user_id": user.id,
        },
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["short_code"]
    assert Url.select().count() == 1
    assert Event.select().where(Event.event_type == "created").count() == 1


def test_post_shorten_rejects_duplicate_active_url(client, user):
    first = client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/new",
            "title": "First",
            "user_id": user.id,
        },
    ).get_json()
    response = client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/new",
            "title": "Second",
            "user_id": user.id,
        },
    )
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["short_code"] == first["short_code"]


def test_post_shorten_rejects_missing_title(client, user):
    response = client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/new",
            "user_id": user.id,
        },
    )
    assert response.status_code == 400


def test_post_shorten_rejects_missing_user(client):
    response = client.post(
        "/shorten",
        json={
            "original_url": "https://example.com/new",
            "title": "New url",
            "user_id": 9999,
        },
    )
    assert response.status_code == 404
