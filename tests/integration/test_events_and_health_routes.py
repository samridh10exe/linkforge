from app.metrics import ERROR_COUNT, REQUEST_COUNT
from app.models import Event, Url
from app.validators import utcnow


def test_get_events_returns_empty_list_when_database_has_no_events(client):
    response = client.get("/events")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload == []


def test_get_events_returns_paginated_slice(client, active_url):
    for index in range(6):
        Event.create(
            url=active_url.id,
            user=active_url.user_id,
            event_type="updated",
            timestamp=utcnow(),
            details={"field": "title", "new_value": f"title-{index}"},
        )

    response = client.get("/events", query_string={"page": 1, "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload) == 5


def test_get_events_rejects_non_integer_page(client):
    response = client.get("/events", query_string={"page": "abc", "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_events_rejects_missing_per_page_when_page_is_present(client):
    response = client.get("/events", query_string={"page": 1})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_events_rejects_non_positive_pagination(client):
    response = client.get("/events", query_string={"page": 0, "per_page": 5})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_pagination"


def test_get_events_for_url_returns_not_found_for_nonexistent_url_id(client):
    response = client.get("/events/9999")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "url_not_found"


def test_get_events_for_url_returns_events_for_existing_url(client, active_url):
    Event.create(
        url=active_url.id,
        user=active_url.user_id,
        event_type="updated",
        timestamp=utcnow(),
        details={"field": "title", "new_value": "updated"},
    )

    response = client.get(f"/events/{active_url.id}")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload) == 2
    assert payload[0]["url_id"] == active_url.id


def test_get_ready_returns_exact_status_ready(client):
    response = client.get("/ready")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload == {"status": "ready"}


def test_get_metrics_returns_prometheus_text_and_active_url_count(client, active_url):
    Url.create(
        user=active_url.user_id,
        short_code="def456",
        original_url="https://example.com/second",
        title="Second",
        is_active=False,
        expires_at=None,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/plain")
    assert "# HELP request_count_total HTTP request count" in body
    assert "active_urls_total 1.0" in body


def test_request_counter_increments_after_health_request(client):
    counter = REQUEST_COUNT.labels("GET", "/health", "200")
    before = counter._value.get()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert counter._value.get() == before + 1


def test_error_counter_increments_after_user_not_found_response(client):
    counter = ERROR_COUNT.labels("/users/<int:user_id>", "404")
    before = counter._value.get()

    response = client.get("/users/9999")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "user_not_found"
    assert counter._value.get() == before + 1
