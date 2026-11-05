from flask import current_app, render_template
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from .extensions import appbuilder
from .models import Categoria, Cliente, Ingrediente, Producto, Receta


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


class RecetaView(ModelView):
    datamodel = SQLAInterface(Receta)

    label_columns = {
        "producto": "Producto",
        "ingrediente": "Ingrediente",
        "cantidad": "Cantidad",
        "subtotal": "Costo (Bs)",
    }

    list_columns = ["producto", "ingrediente", "cantidad", "subtotal"]
    show_columns = ["id", "producto", "ingrediente", "cantidad", "subtotal"]
    add_columns = ["producto", "ingrediente", "cantidad"]
    edit_columns = add_columns
    search_columns = ["producto", "ingrediente"]
    order_columns = ["cantidad"]


class IngredienteView(ModelView):
    datamodel = SQLAInterface(Ingrediente)
    # Muestra en qué productos se usa el ingrediente
    related_views = [RecetaView]

    label_columns = {
        "nombre": "Nombre",
        "unidad_medida": "Unidad de medida",
        "costo_unitario": "Costo por unidad (Bs)",
        "activo": "Activo",
    }

    list_columns = ["nombre", "unidad_medida", "costo_unitario", "activo"]
    show_columns = ["id", "nombre", "unidad_medida", "costo_unitario", "activo"]
    add_columns = ["nombre", "unidad_medida", "costo_unitario", "activo"]
    edit_columns = add_columns
    search_columns = ["nombre", "unidad_medida", "activo"]
    order_columns = ["nombre", "costo_unitario"]


class ProductoView(ModelView):
    datamodel = SQLAInterface(Producto)
    # En el detalle del producto se ve y se arma su receta
    related_views = [RecetaView]

    label_columns = {
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "categoria": "Categoría",
        "precio_venta": "Precio de venta (Bs)",
        "margen_ganancia": "Ganancia (%)",
        "costo": "Costo (Bs)",
        "precio_sugerido": "Precio sugerido (Bs)",
        "activo": "Activo",
    }

    list_columns = [
        "nombre",
        "categoria",
        "costo",
        "precio_sugerido",
        "precio_venta",
        "activo",
    ]
    show_columns = [
        "id",
        "nombre",
        "categoria",
        "descripcion",
        "costo",
        "margen_ganancia",
        "precio_sugerido",
        "precio_venta",
        "activo",
    ]
    add_columns = [
        "nombre",
        "categoria",
        "descripcion",
        "margen_ganancia",
        "precio_venta",
        "activo",
    ]
    edit_columns = add_columns
    description_columns = {
        "margen_ganancia": "Porcentaje que se suma al costo de la receta "
        "para calcular el precio sugerido.",
    }
    search_columns = ["nombre", "categoria", "precio_venta", "activo"]
    order_columns = ["nombre", "precio_venta"]


class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    # Muestra los productos de la categoría al ver su detalle
    related_views = [ProductoView]

    label_columns = {
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "activo": "Activo",
        "productos": "Productos",
    }

    list_columns = ["nombre", "descripcion", "activo"]
    show_columns = ["id", "nombre", "descripcion", "activo"]
    add_columns = ["nombre", "descripcion", "activo"]
    edit_columns = add_columns
    search_columns = ["nombre", "activo"]
    order_columns = ["nombre"]


appbuilder.add_view(
    ClienteView,
    "Clientes",
    icon="fa-users",
    category="Ventas",
    category_icon="fa-shopping-cart",
)
appbuilder.add_view(
    CategoriaView,
    "Categorías",
    icon="fa-tags",
    category="Inventario",
    category_icon="fa-archive",
)
appbuilder.add_view(
    ProductoView,
    "Productos",
    icon="fa-coffee",
    category="Inventario",
)
appbuilder.add_view(
    IngredienteView,
    "Ingredientes",
    icon="fa-cubes",
    category="Inventario",
)
appbuilder.add_view(
    RecetaView,
    "Recetas y costos",
    icon="fa-list-alt",
    category="Inventario",
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
