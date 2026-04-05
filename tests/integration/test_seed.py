from app.models import Event, Url, User
from scripts.seed import load_seed_data


def test_seed_is_idempotent(app):
    with app.app_context():
        load_seed_data(config=app.config)
        load_seed_data(config=app.config)

        assert User.select().count() == 400
        assert Url.select().count() == 2000
        assert Event.select().count() == 3422
