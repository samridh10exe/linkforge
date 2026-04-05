import io

from app.models import Url, User
from app.validators import utcnow


def test_get_urls_rejects_non_integer_user_id(client):
    response = client.get("/urls", query_string={"user_id": "abc"})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_user_id"


def test_get_urls_rejects_non_integer_pagination(client):
    response = client.get("/urls", query_string={"page": "abc", "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_urls_returns_paginated_slice_for_valid_pagination(client, user):
    for index in range(2):
        client.post(
            "/urls",
            json={
                "user_id": user.id,
                "original_url": f"https://example.com/paginated-{index}",
                "title": f"Paginated {index}",
            },
        )

    response = client.get("/urls", query_string={"page": 1, "per_page": 1})
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["id"] == 1


def test_get_urls_rejects_non_positive_pagination(client):
    response = client.get("/urls", query_string={"page": 0, "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_url_returns_not_found_for_nonexistent_id(client):
    response = client.get("/urls/9999")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "url_not_found"


def test_put_url_returns_not_found_for_nonexistent_id(client):
    response = client.put("/urls/9999", json={"title": "Updated"})
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "url_not_found"


def test_put_url_returns_missing_json_body_for_empty_body(client, active_url):
    response = client.put(f"/urls/{active_url.id}", data="")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "missing_json_body"


def test_delete_short_code_returns_not_found_for_nonexistent_code(client, user):
    response = client.delete(
        "/missing1",
        json={"user_id": user.id, "reason": "user_requested"},
    )
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "short_code_not_found"


def test_delete_short_code_returns_gone_for_inactive_code(client, active_url):
    Url.update(is_active=False).where(Url.id == active_url.id).execute()
    response = client.delete(
        f"/{active_url.short_code}",
        json={"user_id": active_url.user_id, "reason": "user_requested"},
    )
    payload = response.get_json()

    assert response.status_code == 410
    assert payload["error"]["code"] == "short_code_inactive"


def test_post_shorten_returns_same_fields_as_post_urls(client, user):
    shorten_response = client.post(
        "/shorten",
        json={
            "user_id": user.id,
            "original_url": "https://example.com/alias-shorten",
            "title": "Alias Shorten",
        },
    )
    url_response = client.post(
        "/urls",
        json={
            "user_id": user.id,
            "original_url": "https://example.com/alias-urls",
            "title": "Alias Urls",
        },
    )
    shorten_payload = shorten_response.get_json()
    url_payload = url_response.get_json()

    assert shorten_response.status_code == 201
    assert url_response.status_code == 201
    assert set(shorten_payload.keys()) == set(url_payload.keys())
    assert shorten_payload["user_id"] == user.id
    assert url_payload["user_id"] == user.id


def test_get_user_returns_not_found_for_nonexistent_id(client):
    response = client.get("/users/9999")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "user_not_found"


def test_put_user_returns_not_found_for_nonexistent_id(client):
    response = client.put("/users/9999", json={"username": "updated"})
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "user_not_found"


def test_put_user_returns_conflict_when_email_already_exists(client):
    first = client.post("/users", json={"username": "first", "email": "first@example.com"}).get_json()
    second = client.post("/users", json={"username": "second", "email": "second@example.com"}).get_json()

    response = client.put(
        f"/users/{second['id']}",
        json={"email": first["email"]},
    )
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "email_conflict"


def test_post_users_bulk_returns_missing_file_error_when_file_absent(client):
    response = client.post("/users/bulk", data={}, content_type="multipart/form-data")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "missing_file"


def test_post_users_bulk_returns_zero_when_all_rows_conflict(client):
    csv_body = (
        "id,username,email,created_at\n"
        "1,bulkuser1,bulkuser1@example.com,2026-04-03 12:00:00\n"
        "2,bulkuser2,bulkuser2@example.com,2026-04-03 12:01:00\n"
    )
    first = client.post(
        "/users/bulk",
        data={"file": (io.BytesIO(csv_body.encode("utf-8")), "users.csv")},
        content_type="multipart/form-data",
    )
    second = client.post(
        "/users/bulk",
        data={"file": (io.BytesIO(csv_body.encode("utf-8")), "users.csv")},
        content_type="multipart/form-data",
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.get_json()["count"] == 0
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_users_rejects_non_integer_pagination(client):
    response = client.get("/users", query_string={"page": "abc", "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_users_returns_paginated_slice_for_valid_pagination(client):
    client.post("/users", json={"username": "first", "email": "first@example.com"})
    client.post("/users", json={"username": "second", "email": "second@example.com"})

    response = client.get("/users", query_string={"page": 1, "per_page": 1})
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["username"] == "first"


def test_get_users_rejects_non_positive_pagination(client):
    response = client.get("/users", query_string={"page": 0, "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"
