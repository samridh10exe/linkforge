from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import request

from app.errors import APIError

DELETE_REASONS = {"user_requested", "policy_cleanup", "expired", "duplicate"}


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def parse_json_body():
    if request.data in {b"", None}:
        raise APIError(400, "missing_json_body", "Request body is required")
    if not request.is_json:
        raise APIError(400, "invalid_content_type", "Content-Type must be application/json")
    try:
        payload = request.get_json(force=True)
    except Exception as exc:
        raise APIError(400, "malformed_json", "Malformed JSON body") from exc
    if not isinstance(payload, dict):
        raise APIError(400, "invalid_json_body", "JSON body must be an object")
    return payload


def parse_timestamp(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise APIError(400, f"invalid_{field_name}", f"{field_name} must be a valid timestamp")
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise APIError(400, f"invalid_{field_name}", f"{field_name} must be a valid timestamp") from exc
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def validate_original_url(value):
    if value is None:
        raise APIError(400, "missing_original_url", "original_url is required")
    if not isinstance(value, str):
        raise APIError(400, "invalid_original_url", "original_url must be a string")
    value = value.strip()
    if not value:
        raise APIError(400, "invalid_original_url", "original_url cannot be blank")
    if len(value) > 2048:
        raise APIError(400, "invalid_original_url", "original_url must be 2048 characters or fewer")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise APIError(400, "invalid_original_url", "original_url must use http or https")
    if not parsed.netloc:
        raise APIError(400, "invalid_original_url", "original_url must include a hostname")
    return value


def validate_title(value):
    if value is None:
        raise APIError(400, "missing_title", "title is required")
    if not isinstance(value, str):
        raise APIError(400, "invalid_title", "title must be a string")
    value = value.strip()
    if not value:
        raise APIError(400, "invalid_title", "title cannot be blank")
    return value


def validate_user_id(value):
    if value is None:
        raise APIError(400, "missing_user_id", "user_id is required")
    if isinstance(value, bool) or not isinstance(value, int):
        raise APIError(400, "invalid_user_id", "user_id must be an integer")
    return value


def validate_shorten_payload():
    payload = parse_json_body()
    expires_at = parse_timestamp(payload.get("expires_at"), "expires_at")
    if expires_at is not None and expires_at <= utcnow():
        raise APIError(400, "invalid_expires_at", "expires_at must be in the future")
    return {
        "original_url": validate_original_url(payload.get("original_url")),
        "title": validate_title(payload.get("title")),
        "user_id": validate_user_id(payload.get("user_id")),
        "expires_at": expires_at,
    }


def validate_delete_payload():
    payload = parse_json_body()
    reason = payload.get("reason")
    if reason is None:
        raise APIError(400, "missing_reason", "reason is required")
    if reason not in DELETE_REASONS:
        raise APIError(400, "invalid_reason", "reason is invalid")
    return {
        "user_id": validate_user_id(payload.get("user_id")),
        "reason": reason,
    }
