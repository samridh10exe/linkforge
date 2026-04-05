from flask import Flask
from peewee import OperationalError

from app.errors import APIError, register_error_handlers


def test_api_error_uses_structured_envelope():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/boom")
    def boom():
        raise APIError(410, "short_code_inactive", "URL is no longer active")

    response = app.test_client().get("/boom")
    payload = response.get_json()

    assert response.status_code == 410
    assert payload["error"]["code"] == "short_code_inactive"
    assert payload["error"]["message"] == "URL is no longer active"
    assert "request_id" in payload["error"]


def test_http_exception_uses_route_not_found_envelope():
    app = Flask(__name__)
    register_error_handlers(app)

    response = app.test_client().get("/missing")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "route_not_found"
    assert payload["error"]["message"] == "Route not found"


def test_operational_error_uses_database_unavailable_envelope():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/db")
    def db_failure():
        raise OperationalError("db down")

    response = app.test_client().get("/db")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["error"]["code"] == "database_unavailable"
    assert payload["error"]["message"] == "Database is unavailable"


def test_unexpected_exception_uses_internal_server_error_envelope():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("unexpected")

    response = app.test_client().get("/boom")
    payload = response.get_json()

    assert response.status_code == 500
    assert payload["error"]["code"] == "internal_server_error"
    assert payload["error"]["message"] == "Internal server error"
