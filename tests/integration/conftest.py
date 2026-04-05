import os

import pytest

from app import create_app
from app.database import close_db, connect_db, db
from app.models import Event, Url, User
from app.validators import utcnow
from scripts.bootstrap_db import bootstrap


@pytest.fixture(scope="session")
def app():
    config = {
        "TESTING": True,
        "DATABASE_NAME": os.getenv("TEST_DATABASE_NAME", os.getenv("DATABASE_NAME", "postgres")),
        "DATABASE_HOST": os.getenv("DATABASE_HOST", "localhost"),
        "DATABASE_PORT": int(os.getenv("DATABASE_PORT", "5432")),
        "DATABASE_USER": os.getenv("DATABASE_USER", "postgres"),
        "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", "postgres"),
    }
    app = create_app(config)
    with app.app_context():
        bootstrap(app.config)
    return app


@pytest.fixture(autouse=True)
def clean_db(app, monkeypatch):
    with app.app_context():
        connect_db()
        db.execute_sql("TRUNCATE TABLE events, urls, users RESTART IDENTITY CASCADE")
    monkeypatch.setattr("app.routes.urls.enqueue_click_event", lambda *args, **kwargs: None)
    yield
    with app.app_context():
        close_db()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        return User.create(
            username="alice",
            email="alice@example.com",
            created_at=utcnow(),
        )


@pytest.fixture
def active_url(app, user):
    with app.app_context():
        url = Url.create(
            user=user.id,
            short_code="abc123",
            original_url="https://example.com/path",
            title="Example",
            is_active=True,
            expires_at=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        Event.create(
            url=url.id,
            user=user.id,
            event_type="created",
            timestamp=utcnow(),
            details={"short_code": url.short_code, "original_url": url.original_url},
        )
        return url
