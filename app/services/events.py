from concurrent.futures import ThreadPoolExecutor

from flask import current_app

from app.database import db
from app.metrics import mark_click_event_enqueue_failure
from app.models.event import Event
from app.validators import utcnow

_executor = None


def _get_executor():
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=current_app.config["CLICK_EVENT_WORKERS"],
            thread_name_prefix="click-events",
        )
    return _executor


def create_event(url_id, user_id, event_type, details):
    Event.create(
        url=url_id,
        user=user_id,
        event_type=event_type,
        timestamp=utcnow(),
        details=details,
    )


def enqueue_click_event(url_id, user_id, details):
    try:
        executor = _get_executor()
        executor.submit(_write_click_event, url_id, user_id, details)
    except Exception:
        mark_click_event_enqueue_failure()


def _write_click_event(url_id, user_id, details):
    try:
        with db.connection_context():
            create_event(url_id, user_id, "clicked", details)
    except Exception:
        mark_click_event_enqueue_failure()
