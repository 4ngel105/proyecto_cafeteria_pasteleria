from flask import Flask

from .extensions import appbuilder, db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config")
    db.init_app(app)
    with app.app_context():
        appbuilder.init_app(app, db.session)
        # Registrar modelos y vistas
        from . import models, views  # noqa: F401
    return app
