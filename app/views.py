from flask import current_app, render_template
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from .extensions import appbuilder
from .models import Cliente, Producto


class ClienteView(ModelView):
    datamodel = SQLAInterface(Cliente)

    label_columns = {
        "nombre": "Nombre",
        "apellido": "Apellido",
        "ci_nit": "CI / NIT",
        "telefono": "Teléfono",
        "email": "Correo",
        "fecha_registro": "Fecha de registro",
        "activo": "Activo",
    }

    list_columns = ["nombre", "apellido", "ci_nit", "telefono", "activo"]
    show_columns = [
        "id",
        "nombre",
        "apellido",
        "ci_nit",
        "telefono",
        "email",
        "fecha_registro",
        "activo",
    ]
    add_columns = ["nombre", "apellido", "ci_nit", "telefono", "email", "activo"]
    edit_columns = add_columns
    search_columns = ["nombre", "apellido", "ci_nit"]
    order_columns = ["nombre", "apellido", "fecha_registro"]


class ProductoView(ModelView):
    datamodel = SQLAInterface(Producto)

    label_columns = {
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "precio_venta": "Precio de venta (Bs)",
        "activo": "Activo",
    }

    list_columns = ["nombre", "precio_venta", "activo"]
    show_columns = ["id", "nombre", "descripcion", "precio_venta", "activo"]
    add_columns = ["nombre", "descripcion", "precio_venta", "activo"]
    edit_columns = add_columns
    search_columns = ["nombre", "precio_venta", "activo"]
    order_columns = ["nombre", "precio_venta"]


appbuilder.add_view(
    ClienteView,
    "Clientes",
    icon="fa-users",
    category="Ventas",
    category_icon="fa-shopping-cart",
)
appbuilder.add_view(
    ProductoView,
    "Productos",
    icon="fa-coffee",
    category="Inventario",
    category_icon="fa-archive",
)


"""
    Application wide 404 error handler
"""


@current_app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )
