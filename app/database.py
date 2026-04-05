from flask import request
from peewee import DatabaseProxy, Model, OperationalError
from playhouse.pool import PooledPostgresqlExtDatabase

db = DatabaseProxy()
_schema_ready = False


class BaseModel(Model):
    class Meta:
        database = db


def build_database(app_config):
    return PooledPostgresqlExtDatabase(
        app_config["DATABASE_NAME"],
        host=app_config["DATABASE_HOST"],
        port=app_config["DATABASE_PORT"],
        user=app_config["DATABASE_USER"],
        password=app_config["DATABASE_PASSWORD"],
        connect_timeout=2,
        max_connections=app_config["DATABASE_MAX_CONNECTIONS"],
        stale_timeout=app_config["DATABASE_STALE_TIMEOUT"],
        timeout=app_config["DATABASE_POOL_TIMEOUT"],
        autorollback=True,
    )


def init_database(app_config):
    database = build_database(app_config)
    db.initialize(database)
    return database


def connect_db(reuse_if_open=True):
    if db.is_closed():
        db.connect(reuse_if_open=reuse_if_open)
    if not db.is_connection_usable():
        db.close()
        db.connect(reuse_if_open=reuse_if_open)
        if not db.is_connection_usable():
            raise OperationalError("Database connection is unavailable")
    return db


def close_db():
    if not db.is_closed():
        db.close()


def ensure_schema():
    global _schema_ready
    if _schema_ready:
        return

    from app.models import Event, Url, User

    Event._meta.database.create_tables([User, Url, Event], safe=True)
    # add click_count if missing
    Event._meta.database.execute_sql(
        "ALTER TABLE urls ADD COLUMN IF NOT EXISTS click_count INTEGER NOT NULL DEFAULT 0"
    )
    Event._meta.database.execute_sql(
        "CREATE INDEX IF NOT EXISTS urls_user_created_at_idx ON urls (user_id, created_at DESC)"
    )
    Event._meta.database.execute_sql(
        "CREATE INDEX IF NOT EXISTS urls_active_expires_idx ON urls (is_active, expires_at)"
    )
    Event._meta.database.execute_sql(
        "CREATE INDEX IF NOT EXISTS events_url_timestamp_idx ON events (url_id, timestamp DESC)"
    )
    _schema_ready = True


def init_app_database(app):
    from app.errors import APIError

    init_database(app.config)

    @app.before_request
    def _db_connect():
        if request.endpoint and request.endpoint.startswith("health."):
            return
        try:
            connect_db()
            ensure_schema()
        except OperationalError as exc:
            raise APIError(503, "database_unavailable", "Database is unavailable") from exc

    @app.teardown_appcontext
    def _db_close(exc):
        close_db()
