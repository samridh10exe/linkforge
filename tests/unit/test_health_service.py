from unittest.mock import patch

from flask import Flask

from app.services.health import database_status


def test_database_status_returns_degraded_on_failure():
    app = Flask(__name__)
    app.config.update(
        DATABASE_NAME="hackathon_app",
        DATABASE_HOST="localhost",
        DATABASE_PORT=5432,
        DATABASE_USER="postgres",
        DATABASE_PASSWORD="postgres",
    )

    with app.app_context():
        with patch("app.services.health.psycopg2.connect", side_effect=RuntimeError("boom")):
            assert database_status(1000) == "degraded"


def test_database_status_returns_connected_on_success():
    app = Flask(__name__)
    app.config.update(
        DATABASE_NAME="hackathon_app",
        DATABASE_HOST="localhost",
        DATABASE_PORT=5432,
        DATABASE_USER="postgres",
        DATABASE_PASSWORD="postgres",
    )

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, sql):
            self.sql = sql

        def fetchone(self):
            return (1,)

    class FakeConnection:
        def __init__(self):
            self.closed = False
            self.cursor_obj = FakeCursor()

        def cursor(self):
            return self.cursor_obj

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()

    with app.app_context():
        with patch("app.services.health.psycopg2.connect", return_value=fake_connection):
            assert database_status(1000) == "connected"
    assert fake_connection.closed is True
    assert fake_connection.cursor_obj.sql == "SELECT 1"
