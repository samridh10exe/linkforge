from app.routes.events import events_bp
from app.routes.health import health_bp
from app.routes.users import users_bp
from app.routes.urls import urls_bp


def register_routes(app):
    app.register_blueprint(events_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(urls_bp)
