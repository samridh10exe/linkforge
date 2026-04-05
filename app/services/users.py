from peewee import IntegrityError

from app.database import db
from app.errors import APIError
from app.models.user import User
from app.validators import parse_timestamp, utcnow


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


def _validate_username(value, *, required):
    if value is None:
        if required:
            raise APIError(400, "missing_username", "username is required")
        return None
    if not isinstance(value, str):
        raise APIError(400, "invalid_username", "username must be a string")
    value = value.strip()
    if not value:
        raise APIError(400, "invalid_username", "username cannot be blank")
    return value


def _validate_email(value, *, required):
    if value is None:
        if required:
            raise APIError(400, "missing_email", "email is required")
        return None
    if not isinstance(value, str):
        raise APIError(400, "invalid_email", "email must be a string")
    value = value.strip()
    if not value or "@" not in value:
        raise APIError(400, "invalid_email", "email must be a valid email address")
    return value


def get_user_by_id(user_id):
    user = User.get_or_none(User.id == user_id)
    if user is None:
        raise APIError(404, "user_not_found", "User does not exist")
    return user


def list_users(*, page=None, per_page=None):
    query = User.select().order_by(User.id.asc())
    if page is not None and per_page is not None:
        query = query.paginate(page, per_page)
    return list(query)


def create_user(username, email, *, user_id=None, created_at=None):
    username = _validate_username(username, required=True)
    email = _validate_email(email, required=True)
    # upsert: return existing on duplicate email
    existing = User.get_or_none(User.email == email)
    if existing is not None:
        if existing.username != username:
            User.update(username=username).where(User.id == existing.id).execute()
            return User.get_by_id(existing.id)
        return existing
    created_at = parse_timestamp(created_at, "created_at") if created_at is not None else utcnow()
    payload = {
        "username": username,
        "email": email,
        "created_at": created_at,
    }
    if user_id is not None:
        payload["id"] = int(user_id)
    try:
        with db.atomic():
            return User.create(**payload)
    except IntegrityError:
        # race condition fallback
        existing = User.get_or_none(User.email == email)
        if existing is not None:
            return existing
        raise APIError(409, "email_conflict", "Email already exists")


def update_user(user_id, payload):
    user = get_user_by_id(user_id)
    updates = {}

    if "username" in payload:
        updates["username"] = _validate_username(payload.get("username"), required=False)
    if "email" in payload:
        updates["email"] = _validate_email(payload.get("email"), required=False)
    if not updates:
        raise APIError(400, "empty_update", "At least one field is required")

    try:
        with db.atomic():
            User.update(**updates).where(User.id == user.id).execute()
    except IntegrityError as exc:
        raise APIError(409, "email_conflict", "Email already exists") from exc
    return get_user_by_id(user.id)


def bulk_import_users(rows):
    payloads = []
    for row in rows:
        payload = {
            "username": _validate_username(row.get("username"), required=True),
            "email": _validate_email(row.get("email"), required=True),
            "created_at": parse_timestamp(row.get("created_at"), "created_at")
            if row.get("created_at")
            else utcnow(),
        }
        if row.get("id"):
            payload["id"] = int(row["id"])
        payloads.append(payload)

    before = User.select().count()
    with db.atomic():
        User.insert_many(payloads).on_conflict_ignore().execute()
    after = User.select().count()
    return after - before


def delete_user(user_id):
    user = get_user_by_id(user_id)
    from app.models.event import Event
    from app.models.url import Url

    with db.atomic():
        Event.delete().where(Event.user == user.id).execute()
        Url.delete().where(Url.user == user.id).execute()
        User.delete().where(User.id == user.id).execute()
