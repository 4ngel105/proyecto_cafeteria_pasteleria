from flask import current_app, redirect, render_template, url_for
from flask_appbuilder import ModelView
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from markupsafe import Markup
from wtforms.validators import NumberRange

from .extensions import appbuilder
from .models import (
    Categoria,
    Cliente,
    DetalleVenta,
    Ingrediente,
    Producto,
    Receta,
    Venta,
)
from .pantallas import AsistenteIAView, NuevaVentaView, RecetaFormView


def si_no(valor):
    """Muestra Sí / No en lugar de True / False."""
    if valor:
        return Markup('<span class="label label-success">Sí</span>')
    return Markup('<span class="label label-default">No</span>')


class RecetaView(ModelView):
    datamodel = SQLAInterface(Receta)
    list_title = "Recetas"
    show_title = "Detalle de la receta"
    add_title = "Nueva receta"
    edit_title = "Editar receta"
    # Solo lectura: la receta se arma desde la pantalla "Recetas y costos"
    base_permissions = ["can_list", "can_show"]

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
    list_title = "Ingredientes"
    show_title = "Detalle del ingrediente"
    add_title = "Nuevo ingrediente"
    edit_title = "Editar ingrediente"
    formatters_columns = {"activo": si_no}
    # Muestra en qué productos se usa el ingrediente
    related_views = [RecetaView]

    label_columns = {
        "nombre": "Nombre",
        "presentacion": "Presentación",
        "contenido": "Contenido",
        "unidad_medida": "Unidad",
        "precio_compra": "Precio de compra (Bs)",
        "costo_unitario": "Costo por unidad (Bs)",
        "activo": "Activo",
    }

    list_columns = [
        "nombre",
        "presentacion",
        "contenido",
        "unidad_medida",
        "precio_compra",
        "costo_unitario",
        "activo",
    ]
    show_columns = ["id"] + list_columns
    add_columns = [
        "nombre",
        "presentacion",
        "contenido",
        "unidad_medida",
        "precio_compra",
        "activo",
    ]
    edit_columns = add_columns
    search_columns = ["nombre", "presentacion", "unidad_medida", "activo"]
    order_columns = ["nombre", "precio_compra"]
    description_columns = {
        "presentacion": "Cómo lo compras. Ej: Lata, Bolsa, Caja.",
        "contenido": "Cuánto trae, en la unidad elegida. Ej: 200 (si la lata trae 200 g).",
        "unidad_medida": "La unidad que usarás en las recetas. Ej: g.",
        "precio_compra": "Lo que pagas por la presentación completa. Ej: 30.",
    }
    validators_columns = {
        "contenido": [NumberRange(min=0.001, message="El contenido debe ser mayor a 0")],
        "precio_compra": [NumberRange(min=0, message="El precio no puede ser negativo")],
    }


class ProductoView(ModelView):
    datamodel = SQLAInterface(Producto)
    list_title = "Productos"
    show_title = "Detalle del producto"
    add_title = "Nuevo producto"
    edit_title = "Editar producto"
    formatters_columns = {"activo": si_no}
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

    @action(
        "armar_receta",
        "Armar receta",
        icon="fa-list-alt",
        multiple=False,
        single=True,
    )
    def armar_receta(self, items):
        # Desde el detalle llega una lista con un solo producto
        item = items[0] if isinstance(items, list) else items
        return redirect(url_for("RecetaFormView.editar", pk=item.id))


class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    list_title = "Categorías"
    show_title = "Detalle de la categoría"
    add_title = "Nueva categoría"
    edit_title = "Editar categoría"
    formatters_columns = {"activo": si_no}
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


class DetalleVentaView(ModelView):
    datamodel = SQLAInterface(DetalleVenta)
    list_title = "Productos vendidos"
    show_title = "Detalle del producto vendido"
    add_title = "Agregar producto"
    edit_title = "Editar producto vendido"
    # Los productos de una venta se cargan desde "Nueva venta"; aquí solo se
    # consultan, y se puede corregir una línea (por ejemplo, un descuento)
    base_permissions = ["can_list", "can_show", "can_edit", "can_delete"]

    label_columns = {
        "venta": "Venta",
        "producto": "Producto",
        "cantidad": "Cantidad",
        "precio_unitario": "Precio unitario (Bs)",
        "subtotal": "Subtotal (Bs)",
    }

    list_columns = ["venta", "producto", "cantidad", "precio_unitario", "subtotal"]
    show_columns = [
        "id",
        "venta",
        "producto",
        "cantidad",
        "precio_unitario",
        "subtotal",
    ]
    edit_columns = ["producto", "cantidad", "precio_unitario"]
    search_columns = ["venta", "producto"]
    order_columns = ["cantidad", "precio_unitario"]
    validators_columns = {
        "cantidad": [NumberRange(min=1, message="La cantidad debe ser al menos 1")],
    }


class VentaView(ModelView):
    datamodel = SQLAInterface(Venta)
    list_title = "Historial de ventas"
    show_title = "Detalle de la venta"
    add_title = "Nueva venta"
    edit_title = "Editar venta"
    # Las ventas nuevas se registran desde "Nueva venta"
    base_permissions = ["can_list", "can_show", "can_edit", "can_delete"]
    # En el detalle de la venta se ven sus productos
    related_views = [DetalleVentaView]

    label_columns = {
        "id": "N°",
        "fecha": "Fecha",
        "cliente": "Cliente",
        "metodo_pago": "Método de pago",
        "total": "Total (Bs)",
    }

    list_columns = ["id", "fecha", "cliente", "metodo_pago", "total"]
    show_columns = ["id", "fecha", "cliente", "metodo_pago", "total"]
    edit_columns = ["fecha", "cliente", "metodo_pago"]
    search_columns = ["fecha", "cliente", "metodo_pago"]
    order_columns = ["id", "fecha"]
    base_order = ("fecha", "desc")
    description_columns = {
        "cliente": "Déjalo vacío si es una venta sin cliente registrado.",
    }


class ClienteView(ModelView):
    datamodel = SQLAInterface(Cliente)
    list_title = "Clientes"
    show_title = "Detalle del cliente"
    add_title = "Nuevo cliente"
    edit_title = "Editar cliente"
    formatters_columns = {"activo": si_no}
    # En el detalle del cliente se ven sus compras
    related_views = [VentaView]

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


appbuilder.add_view(
    NuevaVentaView,
    "Nueva venta",
    icon="fa-cart-plus",
    category="Ventas",
    category_icon="fa-shopping-cart",
)
appbuilder.add_view(
    VentaView,
    "Historial de ventas",
    icon="fa-money",
    category="Ventas",
)
appbuilder.add_view(
    ClienteView,
    "Clientes",
    icon="fa-users",
    category="Ventas",
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
    RecetaFormView,
    "Recetas y costos",
    icon="fa-list-alt",
    category="Inventario",
)
appbuilder.add_view(
    AsistenteIAView,
    "Asistente IA",
    icon="fa-magic",
    category="Asistente IA",
    category_icon="fa-magic",
)
# Sin menú: solo se ven dentro del detalle de producto / venta
appbuilder.add_view_no_menu(RecetaView)
appbuilder.add_view_no_menu(DetalleVentaView)


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
