from flask import Blueprint, jsonify, request

from app.errors import APIError
from app.models.event import Event
from app.services.urls import get_url_by_id

events_bp = Blueprint("events", __name__)


def _serialize_event(event):
    return {
        "id": event.id,
        "url_id": event.url_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
        "details": event.details,
    }


@events_bp.get("/events")
def list_events():
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    query = Event.select().order_by(Event.timestamp.desc(), Event.id.desc())
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
