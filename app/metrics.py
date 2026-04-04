import time

from flask import Response, current_app, g, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.database import db
from app.models.url import Url
from app.validators import utcnow

REQUEST_COUNT = Counter(
    "request_count",
    "HTTP request count",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)
ERROR_COUNT = Counter(
    "error_count",
    "Error response count",
    ["endpoint", "status_code"],
)
REDIRECT_COUNT = Counter("redirect_count", "Successful redirects")
SHORT_CODE_COLLISIONS = Counter("short_code_collision_total", "Short code collisions")
DUPLICATE_URL_CONFLICTS = Counter(
    "duplicate_url_conflict_total", "Duplicate original URL conflicts"
)
CLICK_EVENT_ENQUEUE_FAILURES = Counter(
    "click_event_enqueue_fail_total", "Failed async click event submissions"
)
ACTIVE_URLS_TOTAL = Gauge("active_urls_total", "Active URLs")
DB_POOL_SIZE = Gauge("db_pool_size", "Configured DB pool size")
DB_POOL_IN_USE = Gauge("db_pool_in_use", "DB pool in-use connections")


def install_metrics(app):
    @app.before_request
    def _metrics_start():
        g.metrics_started_at = time.perf_counter()

    @app.after_request
    def _metrics_finish(response):
        endpoint = request.url_rule.rule if request.url_rule else request.path
        duration = time.perf_counter() - getattr(g, "metrics_started_at", time.perf_counter())
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
        if response.status_code >= 400:
            ERROR_COUNT.labels(endpoint, response.status_code).inc()
        return response


def mark_redirect():
    REDIRECT_COUNT.inc()


def mark_collision():
    SHORT_CODE_COLLISIONS.inc()


def mark_duplicate_conflict():
    DUPLICATE_URL_CONFLICTS.inc()


def mark_click_event_enqueue_failure():
    CLICK_EVENT_ENQUEUE_FAILURES.inc()


def render_metrics():
    try:
        ACTIVE_URLS_TOTAL.set(
            Url.select()
            .where(
                (Url.is_active == True)  # noqa: E712
                & ((Url.expires_at.is_null(True)) | (Url.expires_at > utcnow()))
            )
            .count()
        )
    except Exception:
        ACTIVE_URLS_TOTAL.set(0)

    pool = getattr(db.obj, "_in_use", None) if getattr(db, "obj", None) is not None else None
    DB_POOL_SIZE.set(current_app.config["DATABASE_MAX_CONNECTIONS"])
    DB_POOL_IN_USE.set(len(pool) if pool is not None else 0)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
