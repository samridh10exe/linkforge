import hashlib
import json
from datetime import datetime

from peewee import IntegrityError

from app.cache import cache_delete, cache_get, cache_set
from app.database import db
from app.errors import APIError
from app.metrics import mark_collision, mark_duplicate_conflict
from app.models.url import Url
from app.models.user import User
from app.services.events import create_event
from app.services.short_codes import generate_short_code
from app.validators import utcnow, validate_original_url, validate_title


def _lock_key(user_id, original_url):
    digest = hashlib.blake2b(
        f"{user_id}:{original_url}".encode(), digest_size=8
    ).digest()
    return int.from_bytes(digest, byteorder="big", signed=True)


def _active_duplicate_query(user_id, original_url):
    now = utcnow()
    return (
        Url.select()
        .where(
            (Url.user == user_id)
            & (Url.original_url == original_url)
            & (Url.is_active == True)  # noqa: E712
            & ((Url.expires_at.is_null(True)) | (Url.expires_at > now))
        )
        .order_by(Url.id.desc())
    )


def _require_user(user_id):
    user = User.get_or_none(User.id == user_id)
    if user is None:
        raise APIError(404, "user_not_found", "User does not exist")
    return user


def serialize_url_resource(url):
    return {
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "click_count": url.click_count if hasattr(url, "click_count") else 0,
        "expires_at": url.expires_at.isoformat() if url.expires_at else None,
        "created_at": url.created_at.isoformat(),
        "updated_at": url.updated_at.isoformat(),
    }


def create_short_url(original_url, title, user_id, expires_at, *, code_length, max_attempts):
    user = _require_user(user_id)
    now = utcnow()

    with db.atomic():
        db.execute_sql("SELECT pg_advisory_xact_lock(%s)", (_lock_key(user_id, original_url),))
        existing = _active_duplicate_query(user_id, original_url).first()
        if existing is not None:
            mark_duplicate_conflict()
            raise APIError(
                409,
                "url_already_shortened",
                "URL already shortened",
                extra={"short_code": existing.short_code},
            )

        for _ in range(max_attempts):
            short_code = generate_short_code(code_length)
            try:
                url = Url.create(
                    user=user.id,
                    short_code=short_code,
                    original_url=original_url,
                    title=title,
                    is_active=True,
                    expires_at=expires_at,
                    created_at=now,
                    updated_at=now,
                )
                create_event(
                    url.id,
                    user.id,
                    "created",
                    {"short_code": short_code, "original_url": original_url},
                )
                return url
            except IntegrityError:
                mark_collision()
        raise APIError(
            503,
            "short_code_generation_failed",
            "Short code generation failed after max attempts",
        )


def resolve_short_code(short_code):
    # cache hit path
    cached = cache_get(f"url:{short_code}")
    if cached is not None:
        data = json.loads(cached)
        if not data["is_active"]:
            raise APIError(410, "short_code_inactive", "URL is no longer active")
        if data["expires_at"] is not None:
            exp = datetime.fromisoformat(data["expires_at"])
            if exp <= utcnow():
                raise APIError(410, "short_code_expired", "URL is no longer active")
        data["_cache_hit"] = True
        return data

    # cache miss — hit db
    url = Url.get_or_none(Url.short_code == short_code)
    if url is None:
        raise APIError(404, "short_code_not_found", "Short code not found")
    if not url.is_active:
        raise APIError(410, "short_code_inactive", "URL is no longer active")
    if url.expires_at is not None and url.expires_at <= utcnow():
        raise APIError(410, "short_code_expired", "URL is no longer active")

    # populate cache
    cache_set(f"url:{short_code}", json.dumps({
        "id": url.id,
        "user_id": url.user_id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "is_active": url.is_active,
        "expires_at": url.expires_at.isoformat() if url.expires_at else None,
    }))
    return url


def deactivate_short_code(short_code, user_id, reason):
    with db.atomic():
        url = Url.get_or_none(Url.short_code == short_code)
        if url is None:
            raise APIError(404, "short_code_not_found", "Short code not found")
        if not url.is_active or (url.expires_at is not None and url.expires_at <= utcnow()):
            raise APIError(410, "short_code_inactive", "URL is no longer active")
        if url.user_id != user_id:
            raise APIError(403, "forbidden", "User does not own this short code")

        now = utcnow()
        (Url.update(is_active=False, updated_at=now).where(Url.id == url.id).execute())
        create_event(url.id, url.user_id, "deleted", {"reason": reason})
        cache_delete(f"url:{short_code}")
        url.is_active = False
        url.updated_at = now
        return url


def list_user_urls(user_id):
    _require_user(user_id)
    return list(
        Url.select()
        .where(Url.user == user_id)
        .order_by(Url.created_at.desc(), Url.id.desc())
    )


def list_urls(*, user_id=None, is_active=None, page=None, per_page=None):
    query = Url.select().order_by(Url.id.asc())
    if user_id is not None:
        _require_user(user_id)
        query = query.where(Url.user == user_id)
    if is_active is not None:
        query = query.where(Url.is_active == is_active)
    if page is not None and per_page is not None:
        query = query.paginate(page, per_page)
    return list(query)


def get_url_by_id(url_id):
    url = Url.get_or_none(Url.id == url_id)
    if url is None:
        raise APIError(404, "url_not_found", "URL does not exist")
    return url


def update_url_by_id(url_id, payload):
    url = get_url_by_id(url_id)
    updates = {}
    changed = {}

    if "title" in payload:
        updates["title"] = validate_title(payload.get("title"))
        changed["title"] = updates["title"]
    if "original_url" in payload:
        updates["original_url"] = validate_original_url(payload.get("original_url"))
        changed["original_url"] = updates["original_url"]
    if "is_active" in payload:
        value = payload.get("is_active")
        if not isinstance(value, bool):
            raise APIError(400, "invalid_is_active", "is_active must be a boolean")
        updates["is_active"] = value
        changed["is_active"] = value
    if "expires_at" in payload:
        from app.validators import parse_timestamp
        updates["expires_at"] = parse_timestamp(payload.get("expires_at"), "expires_at")
        changed["expires_at"] = str(updates["expires_at"]) if updates["expires_at"] else None

    if not updates:
        raise APIError(400, "empty_update", "At least one field is required")

    now = utcnow()
    updates["updated_at"] = now
    with db.atomic():
        Url.update(**updates).where(Url.id == url.id).execute()
        for field, value in changed.items():
            create_event(url.id, url.user_id, "updated", {"field": field, "new_value": value})
    # invalidate cache on any update
    cache_delete(f"url:{url.short_code}")
    return get_url_by_id(url.id)


def delete_url_by_id(url_id):
    url = get_url_by_id(url_id)
    now = utcnow()
    with db.atomic():
        Url.update(is_active=False, updated_at=now).where(Url.id == url.id).execute()
        create_event(url.id, url.user_id, "deleted", {"reason": "user_requested"})
        cache_delete(f"url:{url.short_code}")
