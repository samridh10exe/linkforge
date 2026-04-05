from dotenv import load_dotenv

from app.config import load_settings
from app.database import close_db, connect_db, init_database
from app.models import Event, Url, User


def bootstrap(config=None):
    load_dotenv()
    settings = load_settings(config)
    init_database(settings.as_dict())
    connect_db()
    try:
        Event._meta.database.create_tables([User, Url, Event], safe=True)
        Event._meta.database.execute_sql(
            "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key"
        )
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
    finally:
        close_db()


if __name__ == "__main__":
    bootstrap()
