from dotenv import load_dotenv
from flask import Flask

from app.config import load_settings
from app.database import init_app_database
from app.errors import register_error_handlers
from app.logging import configure_logging
from app.metrics import install_metrics
from app.routes import register_routes


def create_app(test_config=None):
    load_dotenv()
    settings = load_settings(test_config)

    app = Flask(__name__)
    app.config.update(settings.as_dict())

    configure_logging(app)
    init_app_database(app)
    install_metrics(app)
    register_routes(app)
    register_error_handlers(app)

    return app
