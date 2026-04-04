import csv
import json
from pathlib import Path

from dotenv import load_dotenv

from app.config import load_settings
from app.database import close_db, connect_db, db, init_database
from app.models import Event, Url, User


def _seed_root():
    return Path(__file__).resolve().parents[1] / "Seed Data"


def _parse_bool(value):
    return str(value).strip().lower() == "true"


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _set_sequence(table_name):
    db.execute_sql(
        f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)"
    )


def load_seed_data(seed_dir=None, config=None):
    load_dotenv()
    settings = load_settings(config)
    init_database(settings.as_dict())
    connect_db()
    root = Path(seed_dir) if seed_dir else _seed_root()
    try:
        with db.atomic():
            User.insert_many(
                [
                    {
                        "id": int(row["id"]),
                        "username": row["username"],
                        "email": row["email"],
                        "created_at": row["created_at"],
                    }
                    for row in _rows(root / "users.csv")
                ]
            ).on_conflict_ignore().execute()
            Url.insert_many(
                [
                    {
                        "id": int(row["id"]),
                        "user": int(row["user_id"]),
                        "short_code": row["short_code"],
                        "original_url": row["original_url"],
                        "title": row["title"],
                        "is_active": _parse_bool(row["is_active"]),
                        "expires_at": None,
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                    for row in _rows(root / "urls.csv")
                ]
            ).on_conflict_ignore().execute()
            Event.insert_many(
                [
                    {
                        "id": int(row["id"]),
                        "url": int(row["url_id"]),
                        "user": int(row["user_id"]),
                        "event_type": row["event_type"],
                        "timestamp": row["timestamp"],
                        "details": json.loads(row["details"]),
                    }
                    for row in _rows(root / "events.csv")
                ]
            ).on_conflict_ignore().execute()
        _set_sequence("users")
        _set_sequence("urls")
        _set_sequence("events")
        print(f"Users:  {User.select().count()}")
        print(f"URLs:   {Url.select().count()}")
        print(f"Events: {Event.select().count()}")
    finally:
        close_db()


if __name__ == "__main__":
    load_seed_data()
