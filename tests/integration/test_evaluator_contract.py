import io

from app.models import Event, Url, User
from app.validators import utcnow


def test_health_matches_evaluator_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_users_bulk_list_get_create_update_contract(client):
    csv_body = (
        "id,username,email,created_at\n"
        "11,bulkuser1,bulkuser1@example.com,2026-04-03 12:00:00\n"
        "12,bulkuser2,bulkuser2@example.com,2026-04-03 12:01:00\n"
    )
    response = client.post(
        "/users/bulk",
        data={"file": (io.BytesIO(csv_body.encode("utf-8")), "users.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    assert response.get_json()["count"] == 2

    response = client.get("/users")
    users = response.get_json()
    assert response.status_code == 200
    assert len(users) == 2

    response = client.get("/users/11")
    assert response.status_code == 200
    assert response.get_json()["username"] == "bulkuser1"

    response = client.post(
        "/users",
        json={"username": "created-user", "email": "created-user@example.com"},
    )
    created = response.get_json()
    assert response.status_code == 201
    assert created["username"] == "created-user"

    response = client.put(
        f"/users/{created['id']}",
        json={"username": "updated-user"},
    )
    updated = response.get_json()
    assert response.status_code == 200
    assert updated["username"] == "updated-user"


def test_urls_and_events_contract(client, user):
    response = client.post(
        "/urls",
        json={
            "user_id": user.id,
            "original_url": "https://example.com/contract",
            "title": "Contract URL",
        },
    )
    created = response.get_json()
    assert response.status_code == 201
    assert created["user_id"] == user.id
    assert created["short_code"]

    response = client.get("/urls")
    urls = response.get_json()
    assert response.status_code == 200
    assert len(urls) == 1

    response = client.get(f"/urls/{created['id']}")
    fetched = response.get_json()
    assert response.status_code == 200
    assert fetched["short_code"] == created["short_code"]

    response = client.put(
        f"/urls/{created['id']}",
        json={"title": "Updated Title", "is_active": False},
    )
    updated = response.get_json()
    assert response.status_code == 200
    assert updated["title"] == "Updated Title"
    assert updated["is_active"] is False

    response = client.get("/urls", query_string={"user_id": user.id})
    filtered = response.get_json()
    assert response.status_code == 200
    assert len(filtered) == 1

    response = client.get("/events")
    events = response.get_json()
    assert response.status_code == 200
    assert any(event["event_type"] == "created" for event in events)
    assert any(event["event_type"] == "updated" for event in events)


def test_user_create_rejects_invalid_schema(client):
    response = client.post(
        "/users",
        json={"username": 123, "email": "bad@example.com"},
    )
    assert response.status_code == 400


def test_url_create_rejects_missing_user(client):
    response = client.post(
        "/urls",
        json={
            "user_id": 9999,
            "original_url": "https://example.com/contract",
            "title": "Contract URL",
        },
    )
    assert response.status_code == 404
