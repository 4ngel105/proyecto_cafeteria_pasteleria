"""Pantallas propias: armar la receta de un producto y registrar una venta
en un solo formulario (en vez de ir registro por registro)."""
from decimal import Decimal, InvalidOperation

from flask import abort, flash, redirect, request, url_for
from flask_appbuilder import BaseView, expose, has_access

from .extensions import db
from .models import Cliente, DetalleVenta, Ingrediente, Producto, Receta, Venta

METODOS_PAGO = ["Efectivo", "QR", "Tarjeta"]


def _a_decimal(valor):
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _a_entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _leer_filas(nombre_id, convertir):
    """Lee las filas del formulario (id + cantidad) y junta las repetidas.

    Devuelve (filas, errores). Las filas vacías se ignoran.
    """
    ids = request.form.getlist(nombre_id)
    cantidades = request.form.getlist("cantidad")
    filas, errores = {}, []
    for n, (id_, cant) in enumerate(zip(ids, cantidades), start=1):
        if not id_ and not cant:
            continue
        if not id_:
            errores.append(f"Fila {n}: elige un elemento.")
            continue
        cantidad = convertir(cant)
        if cantidad is None or cantidad <= 0:
            errores.append(f"Fila {n}: la cantidad debe ser mayor a 0.")
            continue
        filas[int(id_)] = filas.get(int(id_), 0) + cantidad
    return filas, errores


class RecetaFormView(BaseView):
    route_base = "/recetas"
    default_view = "lista"

    @expose("/")
    @has_access
    def lista(self):
        productos = (
            db.session.query(Producto).order_by(Producto.nombre).all()
        )
        return self.render_template("receta_lista.html", productos=productos)

    @expose("/<int:pk>", methods=["GET", "POST"])
    @has_access
    def editar(self, pk):
        producto = db.session.get(Producto, pk) or abort(404)
        ingredientes = (
            db.session.query(Ingrediente)
            .filter(Ingrediente.activo.is_(True))
            .order_by(Ingrediente.nombre)
            .all()
        )
        filas = [(r.ingrediente_id, r.cantidad) for r in producto.receta]

        if request.method == "POST":
            nuevas, errores = _leer_filas("ingrediente_id", _a_decimal)
            margen = _a_decimal(request.form.get("margen_ganancia", ""))
            precio = _a_decimal(request.form.get("precio_venta", ""))
            validos = {i.id for i in ingredientes}
            if any(i not in validos for i in nuevas):
                errores.append("Hay un ingrediente que no existe o está inactivo.")
            if margen is None or margen < 0:
                errores.append("La ganancia debe ser un número mayor o igual a 0.")
            if precio is None or precio < 0:
                errores.append("El precio de venta debe ser mayor o igual a 0.")

            if errores:
                for e in errores:
                    flash(e, "danger")
                filas = list(nuevas.items())
            else:
                # Se reemplaza la receta completa por la del formulario
                producto.receta.clear()
                db.session.flush()
                for ingrediente_id, cantidad in nuevas.items():
                    producto.receta.append(
                        Receta(ingrediente_id=ingrediente_id, cantidad=cantidad)
                    )
                producto.margen_ganancia = margen
                producto.precio_venta = precio
                db.session.commit()
                flash(
                    f"Receta de {producto.nombre} guardada. "
                    f"Costo: Bs {producto.costo()} - "
                    f"precio sugerido: Bs {producto.precio_sugerido()}",
                    "success",
                )
                return redirect(url_for("RecetaFormView.lista"))

        return self.render_template(
            "receta_form.html",
            producto=producto,
            ingredientes=ingredientes,
            filas=filas,
        )


class NuevaVentaView(BaseView):
    route_base = "/nueva-venta"
    default_view = "nueva"

    @expose("/", methods=["GET", "POST"])
    @has_access
    def nueva(self):
        clientes = (
            db.session.query(Cliente)
            .filter(Cliente.activo.is_(True))
            .order_by(Cliente.nombre, Cliente.apellido)
            .all()
        )
        productos = (
            db.session.query(Producto)
            .filter(Producto.activo.is_(True))
            .order_by(Producto.nombre)
            .all()
        )
        datos = {"cliente_id": "", "metodo_pago": "Efectivo", "filas": []}

        if request.method == "POST":
            filas, errores = _leer_filas("producto_id", _a_entero)
            cliente_id = request.form.get("cliente_id") or None
            metodo_pago = request.form.get("metodo_pago")
            precios = {p.id: p.precio_venta for p in productos}
            if not filas and not errores:
                errores.append("Agrega al menos un producto.")
            if any(p not in precios for p in filas):
                errores.append("Hay un producto que no existe o está inactivo.")
            if metodo_pago not in METODOS_PAGO:
                errores.append("Elige un método de pago válido.")
            if cliente_id and int(cliente_id) not in {c.id for c in clientes}:
                errores.append("El cliente elegido no existe o está inactivo.")

            if errores:
                for e in errores:
                    flash(e, "danger")
                datos = {
                    "cliente_id": cliente_id or "",
                    "metodo_pago": metodo_pago,
                    "filas": list(filas.items()),
                }
            else:
                venta = Venta(
                    cliente_id=int(cliente_id) if cliente_id else None,
                    metodo_pago=metodo_pago,
                )
                for producto_id, cantidad in filas.items():
                    # El precio se congela al momento de la venta
                    venta.detalles.append(
                        DetalleVenta(
                            producto_id=producto_id,
                            cantidad=cantidad,
                            precio_unitario=precios[producto_id],
                        )
                    )
                db.session.add(venta)
                db.session.commit()
                flash(
                    f"Venta #{venta.id} registrada. Total: Bs {venta.total()}",
                    "success",
                )
                return redirect(url_for("VentaView.show", pk=venta.id))

        return self.render_template(
            "nueva_venta.html",
            clientes=clientes,
            productos=productos,
            metodos=METODOS_PAGO,
            datos=datos,
        )
