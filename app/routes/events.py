from flask import Blueprint, jsonify, request

from app.errors import APIError
from app.models.event import Event
from app.services.events import create_event, normalize_event_type, public_event_type
from app.services.urls import get_url_by_id
from app.services.users import get_user_by_id
from app.validators import parse_json_body

events_bp = Blueprint("events", __name__)


def _serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": public_event_type(event.event_type),
        "timestamp": event.timestamp.isoformat(),
        "details": event.details,
    }


@events_bp.get("/events")
def list_events():
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    query = Event.select().order_by(Event.timestamp.desc(), Event.id.desc())
    url_id = request.args.get("url_id")
    user_id = request.args.get("user_id")
    event_type = request.args.get("event_type")

    if url_id is not None:
        try:
            url_id = int(url_id)
        except ValueError as exc:
            raise APIError(400, "invalid_url_id", "url_id must be an integer") from exc
        query = query.where(Event.url == url_id)

    if user_id is not None:
        try:
            user_id = int(user_id)
        except ValueError as exc:
            raise APIError(400, "invalid_user_id", "user_id must be an integer") from exc
        query = query.where(Event.user == user_id)

    if event_type is not None:
        normalized = normalize_event_type(event_type)
        query = query.where(Event.event_type == normalized)

    if page is not None or per_page is not None:
        if page is None or per_page is None:
            raise APIError(400, "invalid_pagination", "page and per_page must both be provided")
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError as exc:
            raise APIError(400, "invalid_pagination", "page and per_page must be integers") from exc
        if page < 1 or per_page < 1:
            raise APIError(400, "invalid_pagination", "page and per_page must be positive")
        query = query.paginate(page, per_page)
    return jsonify([_serialize_event(event) for event in query])


@events_bp.get("/events/<int:url_id>")
def list_events_for_url(url_id):
    get_url_by_id(url_id)
    query = (
        Event.select()
        .where(Event.url == url_id)
        .order_by(Event.timestamp.desc(), Event.id.desc())
    )
    return jsonify([_serialize_event(event) for event in query])


@events_bp.post("/events")
def post_event():
    payload = parse_json_body()
    url_id = payload.get("url_id")
    user_id = payload.get("user_id")
    event_type = payload.get("event_type")
    details = payload.get("details") or {}

    if not isinstance(url_id, int):
        raise APIError(400, "invalid_url_id", "url_id must be an integer")
    if not isinstance(user_id, int):
        raise APIError(400, "invalid_user_id", "user_id must be an integer")
    if not isinstance(event_type, str) or not event_type.strip():
        raise APIError(400, "invalid_event_type", "event_type is required")
    if not isinstance(details, dict):
        raise APIError(400, "invalid_details", "details must be an object")

    get_url_by_id(url_id)
    get_user_by_id(user_id)
    create_event(url_id, user_id, event_type.strip(), details)
    event = Event.select().order_by(Event.id.desc()).get()
    return jsonify(_serialize_event(event)), 201
