from flask import Blueprint, current_app, jsonify

from app.metrics import render_metrics
from app.services.health import database_status

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@health_bp.get("/ready")
def ready():
    db_status = database_status(current_app.config["HEALTH_DB_TIMEOUT_MS"])
    if db_status != "connected":
        from app.errors import APIError

        raise APIError(503, "database_unavailable", "Database is unavailable")
    return jsonify({"status": "ready"})


@health_bp.get("/metrics")
def metrics():
    return render_metrics()
