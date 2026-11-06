from flask_appbuilder import AppBuilder, Model
from flask_appbuilder.models.sqla.base import SQLA
from flask_wtf.csrf import CSRFProtect

db = SQLA(model_class=Model)
appbuilder = AppBuilder()
# Protege todos los formularios (POST) contra ataques CSRF
csrf = CSRFProtect()
