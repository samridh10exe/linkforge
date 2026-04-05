from datetime import timedelta

import pytest

from app.errors import APIError
from app.metrics import SHORT_CODE_COLLISIONS
from app.models import Event, Url, User
from app.services.urls import (
    create_short_url,
    deactivate_short_code,
    get_url_by_id,
    list_urls,
    list_user_urls,
    resolve_short_code,
    update_url_by_id,
)
from app.validators import utcnow


def test_create_short_url_raises_user_not_found_for_missing_user_id(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_short_url(
                "https://example.com/missing-user",
                "Missing User",
                9999,
                None,
                code_length=6,
                max_attempts=1,
            )
    assert exc.value.status_code == 404
    assert exc.value.code == "user_not_found"


def test_create_short_url_raises_conflict_for_duplicate_active_url_same_user(app, user):
    with app.app_context():
        first = create_short_url(
            "https://example.com/duplicate",
            "First",
            user.id,
            None,
            code_length=6,
            max_attempts=2,
        )
        with pytest.raises(APIError) as exc:
            create_short_url(
                "https://example.com/duplicate",
                "Second",
                user.id,
                None,
                code_length=6,
                max_attempts=2,
            )

    assert exc.value.status_code == 409
    assert exc.value.code == "url_already_shortened"
    assert exc.value.extra["short_code"] == first.short_code


def test_create_short_url_raises_generation_failed_after_short_code_collisions(app, user, monkeypatch):
    with app.app_context():
        Url.create(
            user=user.id,
            short_code="abc123",
            original_url="https://example.com/existing-code",
            title="Existing",
            is_active=True,
            expires_at=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        before = SHORT_CODE_COLLISIONS._value.get()
        monkeypatch.setattr("app.services.urls.generate_short_code", lambda length: "abc123")

        with pytest.raises(APIError) as exc:
            create_short_url(
                "https://example.com/collision",
                "Collision",
                user.id,
                None,
                code_length=6,
                max_attempts=1,
            )

    assert exc.value.status_code == 503
    assert exc.value.code == "short_code_generation_failed"
    assert SHORT_CODE_COLLISIONS._value.get() == before + 1
    assert Url.select().where(Url.original_url == "https://example.com/collision").count() == 0


def test_resolve_short_code_raises_not_found_for_missing_code(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            resolve_short_code("missing1")
    assert exc.value.status_code == 404
    assert exc.value.code == "short_code_not_found"


def test_resolve_short_code_raises_gone_for_inactive_url(app, active_url):
    with app.app_context():
        Url.update(is_active=False).where(Url.id == active_url.id).execute()
        with pytest.raises(APIError) as exc:
            resolve_short_code(active_url.short_code)
    assert exc.value.status_code == 410
    assert exc.value.code == "short_code_inactive"


def test_resolve_short_code_raises_gone_for_expired_url(app, active_url):
    with app.app_context():
        Url.update(expires_at=utcnow() - timedelta(minutes=5)).where(Url.id == active_url.id).execute()
        with pytest.raises(APIError) as exc:
            resolve_short_code(active_url.short_code)
    assert exc.value.status_code == 410
    assert exc.value.code == "short_code_expired"


def test_deactivate_short_code_raises_not_found_for_missing_code(app, user):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            deactivate_short_code("missing1", user.id, "user_requested")
    assert exc.value.status_code == 404
    assert exc.value.code == "short_code_not_found"


def test_deactivate_short_code_raises_forbidden_for_non_owner(app, active_url):
    with app.app_context():
        other = User.create(username="other", email="other@example.com", created_at=utcnow())
        with pytest.raises(APIError) as exc:
            deactivate_short_code(active_url.short_code, other.id, "user_requested")
    assert exc.value.status_code == 403
    assert exc.value.code == "forbidden"


def test_deactivate_short_code_raises_gone_for_inactive_url(app, active_url):
    with app.app_context():
        Url.update(is_active=False).where(Url.id == active_url.id).execute()
        with pytest.raises(APIError) as exc:
            deactivate_short_code(active_url.short_code, active_url.user_id, "user_requested")
    assert exc.value.status_code == 410
    assert exc.value.code == "short_code_inactive"


def test_list_user_urls_raises_not_found_for_missing_user(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            list_user_urls(9999)
    assert exc.value.status_code == 404
    assert exc.value.code == "user_not_found"


def test_list_urls_returns_paginated_slice(app, user):
    with app.app_context():
        for index in range(3):
            Url.create(
                user=user.id,
                short_code=f"a{index}b{index}c{index}",
                original_url=f"https://example.com/{index}",
                title=f"Title {index}",
                is_active=True,
                expires_at=None,
                created_at=utcnow(),
                updated_at=utcnow(),
            )

        rows = list_urls(page=2, per_page=1)

    assert len(rows) == 1
    assert rows[0].original_url == "https://example.com/1"


def test_get_url_by_id_raises_not_found_for_missing_id(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            get_url_by_id(9999)
    assert exc.value.status_code == 404
    assert exc.value.code == "url_not_found"


def test_update_url_by_id_raises_not_found_for_missing_id(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            update_url_by_id(9999, {"title": "Updated"})
    assert exc.value.status_code == 404
    assert exc.value.code == "url_not_found"


def test_update_url_by_id_raises_empty_update_for_empty_payload(app, active_url):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            update_url_by_id(active_url.id, {})
    assert exc.value.status_code == 400
    assert exc.value.code == "empty_update"


def test_update_url_by_id_raises_invalid_is_active_for_non_boolean_value(app, active_url):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            update_url_by_id(active_url.id, {"is_active": "nope"})
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_is_active"


def test_update_url_by_id_updates_original_url_and_creates_updated_event(app, active_url):
    with app.app_context():
        updated = update_url_by_id(active_url.id, {"original_url": "https://example.com/updated"})

    assert updated.original_url == "https://example.com/updated"
    assert Event.select().where(Event.event_type == "updated").count() == 1
    event = Event.get(Event.event_type == "updated")
    assert event.details == {"field": "original_url", "new_value": "https://example.com/updated"}
