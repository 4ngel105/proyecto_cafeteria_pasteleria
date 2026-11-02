from flask_appbuilder import Model

from app import create_app
from app.extensions import db
from app import models  # noqa: F401

app = create_app()

with app.app_context():
    Model.metadata.create_all(db.engine)
    print("Se crearon las tablas:")
    for tabla in Model.metadata.tables:
        print(" -", tabla)
