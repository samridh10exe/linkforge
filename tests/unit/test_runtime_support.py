from unittest.mock import Mock

from flask import Flask, jsonify
from peewee import OperationalError

import app.database as database_module
from app import create_app
from app.config import load_settings
from app.database import connect_db
from app.errors import APIError, register_error_handlers
from app.metrics import (
    CLICK_EVENT_ENQUEUE_FAILURES,
    ERROR_COUNT,
    REQUEST_COUNT,
    SHORT_CODE_COLLISIONS,
    install_metrics,
    mark_click_event_enqueue_failure,
    mark_collision,
    render_metrics,
)


def test_load_settings_reads_truthy_testing_env(monkeypatch):
    monkeypatch.setenv("TESTING", "true")
    settings = load_settings()
    assert settings.TESTING is True


def test_connect_db_reconnects_after_unusable_connection(monkeypatch):
    class FakeDb:
        def __init__(self):
            self.usability = iter([False, True])
            self.connect = Mock()
            self.close = Mock()

        def is_closed(self):
            return False

        def is_connection_usable(self):
            return next(self.usability)

    fake_db = FakeDb()
    monkeypatch.setattr(database_module, "db", fake_db)

    result = connect_db()

    assert result is fake_db
    fake_db.close.assert_called_once_with()
    fake_db.connect.assert_called_once_with(reuse_if_open=True)


def test_connect_db_raises_operational_error_when_connection_never_recovers(monkeypatch):
    class FakeDb:
        def __init__(self):
            self.usability = iter([False, False])
            self.connect = Mock()
            self.close = Mock()

        def is_closed(self):
            return False

        def is_connection_usable(self):
            return next(self.usability)

    fake_db = FakeDb()
    monkeypatch.setattr(database_module, "db", fake_db)

    try:
        connect_db()
        assert False, "connect_db should have raised OperationalError"
    except OperationalError as exc:
        assert str(exc) == "Database connection is unavailable"

    fake_db.close.assert_called_once_with()
    fake_db.connect.assert_called_once_with(reuse_if_open=True)


def test_request_counter_increments_after_successful_request():
    app = Flask(__name__)
    install_metrics(app)

    @app.get("/ok")
    def ok():
        return jsonify({"status": "ok"})

    counter = REQUEST_COUNT.labels("GET", "/ok", "200")
    before = counter._value.get()

    response = app.test_client().get("/ok")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert counter._value.get() == before + 1


def test_error_counter_increments_after_client_error_response():
    app = Flask(__name__)
    install_metrics(app)
    register_error_handlers(app)

    @app.get("/fail")
    def fail():
        raise APIError(400, "bad_request", "Bad request")

    counter = ERROR_COUNT.labels("/fail", "400")
    before = counter._value.get()

    response = app.test_client().get("/fail")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "bad_request"
    assert counter._value.get() == before + 1


def test_mark_collision_increments_short_code_collision_counter():
    before = SHORT_CODE_COLLISIONS._value.get()
    mark_collision()
    assert SHORT_CODE_COLLISIONS._value.get() == before + 1


def test_mark_click_event_enqueue_failure_increments_failure_counter():
    before = CLICK_EVENT_ENQUEUE_FAILURES._value.get()
    mark_click_event_enqueue_failure()
    assert CLICK_EVENT_ENQUEUE_FAILURES._value.get() == before + 1


def test_render_metrics_sets_active_urls_to_zero_when_count_query_fails(monkeypatch):
    app = Flask(__name__)
    app.config["DATABASE_MAX_CONNECTIONS"] = 12

    def explode():
        raise RuntimeError("count failed")

    monkeypatch.setattr("app.metrics.Url.select", explode)

    with app.app_context():
        response = render_metrics()
        body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "active_urls_total 0.0" in body
    assert "db_pool_size 12.0" in body


def test_ready_returns_database_unavailable_when_database_is_down():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_NAME": "hackathon_test",
            "DATABASE_HOST": "localhost",
            "DATABASE_PORT": 1,
            "DATABASE_USER": "postgres",
            "DATABASE_PASSWORD": "postgres",
            "HEALTH_DB_TIMEOUT_MS": 1,
        }
    )

    response = app.test_client().get("/ready")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["error"]["code"] == "database_unavailable"
    assert payload["error"]["message"] == "Database is unavailable"


def test_non_health_route_returns_database_unavailable_when_before_request_connection_fails():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_NAME": "hackathon_test",
            "DATABASE_HOST": "localhost",
            "DATABASE_PORT": 1,
            "DATABASE_USER": "postgres",
            "DATABASE_PASSWORD": "postgres",
        }
    )

    response = app.test_client().get("/users")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["error"]["code"] == "database_unavailable"
    assert payload["error"]["message"] == "Database is unavailable"
