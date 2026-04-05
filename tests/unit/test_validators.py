from datetime import timedelta

import pytest
from flask import Flask

from app.errors import APIError
from app.validators import (
    parse_json_body,
    parse_timestamp,
    validate_delete_payload,
    validate_original_url,
    validate_shorten_payload,
    validate_title,
    utcnow,
)


@pytest.fixture
def app():
    return Flask(__name__)


def test_validate_original_url_rejects_missing_scheme():
    with pytest.raises(APIError) as exc:
        validate_original_url("ftp://example.com")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_original_url"


def test_validate_original_url_rejects_missing_value():
    with pytest.raises(APIError) as exc:
        validate_original_url(None)
    assert exc.value.status_code == 400
    assert exc.value.code == "missing_original_url"


def test_validate_original_url_rejects_non_string():
    with pytest.raises(APIError) as exc:
        validate_original_url(123)
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_original_url"


def test_validate_original_url_rejects_blank_string():
    with pytest.raises(APIError) as exc:
        validate_original_url("   ")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_original_url"


def test_validate_original_url_rejects_url_longer_than_2048_characters():
    oversized = "https://example.com/" + ("a" * 2049)
    with pytest.raises(APIError) as exc:
        validate_original_url(oversized)
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_original_url"


def test_validate_original_url_rejects_missing_hostname():
    with pytest.raises(APIError) as exc:
        validate_original_url("https:///missing-host")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_original_url"


def test_validate_title_rejects_non_string():
    with pytest.raises(APIError) as exc:
        validate_title(123)
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_title"


def test_validate_title_rejects_blank_string():
    with pytest.raises(APIError) as exc:
        validate_title("   ")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_title"


def test_parse_json_body_rejects_non_json_content_type(app):
    with app.test_request_context(
        "/users",
        method="POST",
        data='{"username":"alice"}',
        content_type="text/plain",
    ):
        with pytest.raises(APIError) as exc:
            parse_json_body()
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_content_type"


def test_parse_json_body_rejects_malformed_json(app):
    with app.test_request_context(
        "/users",
        method="POST",
        data='{"username":',
        content_type="application/json",
    ):
        with pytest.raises(APIError) as exc:
            parse_json_body()
    assert exc.value.status_code == 400
    assert exc.value.code == "malformed_json"


def test_parse_json_body_rejects_non_object_json(app):
    with app.test_request_context(
        "/users",
        method="POST",
        data='["not","an","object"]',
        content_type="application/json",
    ):
        with pytest.raises(APIError) as exc:
            parse_json_body()
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_json_body"


def test_validate_shorten_payload_requires_body(app):
    with app.test_request_context("/shorten", method="POST", data=""):
        with pytest.raises(APIError) as exc:
            validate_shorten_payload()
    assert exc.value.code == "missing_json_body"


def test_validate_shorten_payload_rejects_missing_user_id(app):
    payload = {
        "original_url": "https://example.com",
        "title": "Example",
    }
    with app.test_request_context("/shorten", method="POST", json=payload):
        with pytest.raises(APIError) as exc:
            validate_shorten_payload()
    assert exc.value.status_code == 400
    assert exc.value.code == "missing_user_id"


def test_validate_shorten_payload_rejects_non_integer_user_id(app):
    payload = {
        "original_url": "https://example.com",
        "title": "Example",
        "user_id": "abc",
    }
    with app.test_request_context("/shorten", method="POST", json=payload):
        with pytest.raises(APIError) as exc:
            validate_shorten_payload()
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_user_id"


def test_validate_shorten_payload_rejects_past_expiry(app):
    payload = {
        "original_url": "https://example.com",
        "title": "Example",
        "user_id": 1,
        "expires_at": (utcnow() - timedelta(hours=1)).isoformat(),
    }
    with app.test_request_context("/shorten", method="POST", json=payload):
        with pytest.raises(APIError) as exc:
            validate_shorten_payload()
    assert exc.value.code == "invalid_expires_at"


def test_parse_timestamp_rejects_blank_string():
    with pytest.raises(APIError) as exc:
        parse_timestamp("   ", "created_at")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_created_at"


def test_parse_timestamp_rejects_malformed_timestamp_string():
    with pytest.raises(APIError) as exc:
        parse_timestamp("not-a-timestamp", "created_at")
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_created_at"


def test_parse_timestamp_normalizes_utc_offset_and_drops_microseconds():
    parsed = parse_timestamp("2026-04-04T12:34:56.999999+02:00", "created_at")
    assert parsed.isoformat() == "2026-04-04T10:34:56"


def test_validate_delete_payload_rejects_empty_body(app):
    with app.test_request_context("/abc123", method="DELETE", data=""):
        with pytest.raises(APIError) as exc:
            validate_delete_payload()
    assert exc.value.code == "missing_json_body"


def test_validate_delete_payload_rejects_missing_reason(app):
    with app.test_request_context(
        "/abc123",
        method="DELETE",
        json={"user_id": 1},
    ):
        with pytest.raises(APIError) as exc:
            validate_delete_payload()
    assert exc.value.status_code == 400
    assert exc.value.code == "missing_reason"


def test_validate_delete_payload_rejects_invalid_reason(app):
    with app.test_request_context(
        "/abc123",
        method="DELETE",
        json={"user_id": 1, "reason": "bogus"},
    ):
        with pytest.raises(APIError) as exc:
            validate_delete_payload()
    assert exc.value.status_code == 400
    assert exc.value.code == "invalid_reason"
