import math

import psycopg2
from flask import current_app


def database_status(timeout_ms):
    timeout_seconds = max(1, math.ceil(int(timeout_ms) / 1000))
    settings = current_app.config
    try:
        connection = psycopg2.connect(
            dbname=settings["DATABASE_NAME"],
            host=settings["DATABASE_HOST"],
            port=settings["DATABASE_PORT"],
            user=settings["DATABASE_USER"],
            password=settings["DATABASE_PASSWORD"],
            connect_timeout=timeout_seconds,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            connection.close()
        return "connected"
    except Exception:
        return "degraded"
