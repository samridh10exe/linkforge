import logging
import time
from uuid import uuid4

from flask import g, has_request_context, request
from pythonjsonlogger.json import JsonFormatter


class RequestFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname.lower())
        if has_request_context():
            log_record.setdefault("request_id", getattr(g, "request_id", None))
            log_record.setdefault("method", request.method)
            log_record.setdefault("path", request.path)


def configure_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(
        RequestFormatter("%(asctime)s %(level)s %(name)s %(message)s")
    )
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    @app.before_request
    def _request_start():
        g.request_id = uuid4().hex
        g.started_at = time.perf_counter()

    @app.after_request
    def _request_log(response):
        duration_ms = round((time.perf_counter() - g.started_at) * 1000, 2)
        app.logger.info(
            "request_complete",
            extra={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
            },
        )
        response.headers["X-Request-ID"] = g.request_id
        return response
