from flask import g, jsonify
from peewee import OperationalError
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    def __init__(self, status_code, code, message, extra=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}


def error_payload(code, message, extra=None):
    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(g, "request_id", "unknown"),
        }
    }
    if extra:
        body["error"].update(extra)
    return body


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def _handle_api_error(exc):
        return jsonify(error_payload(exc.code, exc.message, exc.extra)), exc.status_code

    @app.errorhandler(HTTPException)
    def _handle_http_error(exc):
        code = "route_not_found" if exc.code == 404 else exc.name.lower().replace(" ", "_")
        message = "Route not found" if exc.code == 404 else exc.description
        return jsonify(error_payload(code, message)), exc.code

    @app.errorhandler(OperationalError)
    def _handle_operational_error(exc):
        app.logger.warning("database_unavailable", extra={"error_type": type(exc).__name__})
        return jsonify(error_payload("database_unavailable", "Database is unavailable")), 503

    @app.errorhandler(Exception)
    def _handle_unexpected_error(exc):
        app.logger.exception("request_failed", extra={"error_type": type(exc).__name__})
        return jsonify(error_payload("internal_server_error", "Internal server error")), 500
