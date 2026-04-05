import pytest

from app.errors import APIError
from app.models import User
from app.services.users import (
    _validate_email,
    _validate_username,
    bulk_import_users,
    create_user,
    list_users,
    update_user,
)
from app.validators import utcnow


def test_create_user_raises_missing_username_when_username_absent(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user(None, "missing-username@example.com")
    assert exc.value.status_code == 400
    assert exc.value.code == "missing_username"


def test_create_user_raises_missing_email_when_email_absent(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user("missing-email", None)
    assert exc.value.status_code == 400
    assert exc.value.code == "missing_email"


def test_create_user_raises_invalid_username_when_username_is_integer(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user(123, "invalid-username@example.com")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_username"


def test_create_user_raises_invalid_username_when_username_is_blank(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user("   ", "blank-username@example.com")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_username"


def test_create_user_raises_invalid_email_when_email_has_no_at_sign(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user("invalid-email", "not-an-email")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_email"


def test_create_user_raises_invalid_email_when_email_is_integer(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            create_user("invalid-email-type", 123)
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_email"


def test_validate_username_returns_none_when_optional_value_is_missing():
    assert _validate_username(None, required=False) is None


def test_validate_email_returns_none_when_optional_value_is_missing():
    assert _validate_email(None, required=False) is None


def test_create_user_idempotent_on_duplicate_email(app):
    # idempotent: same email returns existing, updates username if different
    with app.app_context():
        first = create_user("first", "duplicate@example.com")
        second = create_user("second", "duplicate@example.com")
    assert second.id == first.id
    assert second.username == "second"


def test_create_user_recovers_from_stale_unique_username_constraint(app):
    with app.app_context():
        User._meta.database.execute_sql(
            "ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username)"
        )
        try:
            first = create_user("stale-name", "first@example.com")
            second = create_user("stale-name", "second@example.com")
        finally:
            User._meta.database.execute_sql(
                "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key"
            )
    assert second.id == first.id
    assert second.username == "stale-name"
    assert second.email == "second@example.com"


def test_create_user_accepts_explicit_user_id(app):
    with app.app_context():
        user = create_user("explicit-id", "explicit-id@example.com", user_id=77)
    assert user.id == 77
    assert User.select().count() == 1


def test_update_user_raises_not_found_for_missing_user(app):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            update_user(9999, {"username": "updated"})
    assert exc.value.status_code == 404
    assert exc.value.code == "user_not_found"


def test_update_user_raises_empty_update_for_empty_payload(app, user):
    with app.app_context():
        with pytest.raises(APIError) as exc:
            update_user(user.id, {})
    assert exc.value.status_code == 400
    assert exc.value.code == "empty_update"


def test_update_user_raises_conflict_when_email_already_exists(app, user):
    with app.app_context():
        other = User.create(username="other", email="other@example.com", created_at=utcnow())
        with pytest.raises(APIError) as exc:
            update_user(user.id, {"email": other.email})
    assert exc.value.status_code == 409
    assert exc.value.code == "email_conflict"


def test_update_user_updates_email_value(app, user):
    with app.app_context():
        updated = update_user(user.id, {"email": "updated@example.com"})
    assert updated.email == "updated@example.com"
    assert User.get_by_id(user.id).email == "updated@example.com"


def test_list_users_returns_paginated_slice(app):
    with app.app_context():
        create_user("first", "first@example.com")
        create_user("second", "second@example.com")
        create_user("third", "third@example.com")
        rows = list_users(page=2, per_page=1)
    assert len(rows) == 1
    assert rows[0].username == "second"


def test_bulk_import_users_returns_zero_when_all_rows_conflict(app):
    rows = [
        {
            "id": 10,
            "username": "bulk-user",
            "email": "bulk-user@example.com",
            "created_at": utcnow().isoformat(),
        },
        {
            "id": 11,
            "username": "bulk-user-2",
            "email": "bulk-user-2@example.com",
            "created_at": utcnow().isoformat(),
        },
    ]
    with app.app_context():
        first = bulk_import_users(rows)
        second = bulk_import_users(rows)
    assert first == 2
    assert second == 0
    assert User.select().count() == 2
