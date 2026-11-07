"""Pantallas propias: armar la receta de un producto, registrar una venta
en un solo formulario (en vez de ir registro por registro) y el asistente IA."""
from decimal import Decimal, InvalidOperation

from flask import abort, flash, redirect, request, url_for
from flask_appbuilder import BaseView, expose, has_access

from .extensions import db
from .ia import IANoConfigurada, consultar_ia, ia_configurada
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


INSTRUCCIONES_IA = (
    "Eres un asesor de una cafetería-pastelería en Bolivia. Los precios están "
    "en bolivianos (Bs). Responde en español, de forma breve y práctica. "
    "Escribe en texto simple: sin Markdown, sin asteriscos, sin tablas; "
    "para listas usa guiones al inicio de la línea."
)


def _pregunta_precio(producto):
    """Arma la pregunta para sugerir el precio con los datos del producto."""
    lineas = [
        f"Producto: {producto.nombre} (categoría: {producto.categoria}).",
    ]
    if producto.descripcion:
        lineas.append(f"Descripción: {producto.descripcion}.")
    if producto.receta:
        lineas.append("Ingredientes de la receta:")
        for r in producto.receta:
            lineas.append(
                f"- {r.ingrediente.nombre}: {r.cantidad} {r.ingrediente.unidad_medida}"
                f" (costo Bs {r.subtotal()})"
            )
    else:
        lineas.append("Todavía no tiene receta registrada.")
    lineas += [
        f"Costo total de ingredientes: Bs {producto.costo()}.",
        f"Ganancia configurada: {producto.margen_ganancia} %, "
        f"precio sugerido por fórmula: Bs {producto.precio_sugerido()}.",
        f"Precio de venta actual: Bs {producto.precio_venta}.",
        "",
        "¿En cuánto debería venderlo? Da un precio recomendado en Bs, explica "
        "en 2 o 3 frases por qué (costos que faltan como vaso, gas o mano de "
        "obra, y precios habituales en cafeterías) y di si el precio actual "
        "está bien, bajo o alto.",
    ]
    return "\n".join(lineas)


class AsistenteIAView(BaseView):
    route_base = "/asistente"
    default_view = "asistente"

    @expose("/", methods=["GET", "POST"])
    @has_access
    def asistente(self):
        productos = (
            db.session.query(Producto)
            .filter(Producto.activo.is_(True))
            .order_by(Producto.nombre)
            .all()
        )
        modo = request.form.get("modo") or "precio"
        producto_id = request.values.get("producto", type=int)
        texto_libre = request.form.get("pregunta", "").strip()
        pregunta = respuesta = aviso = None

        if request.method == "POST":
            if modo == "precio":
                producto = db.session.get(Producto, producto_id) if producto_id else None
                if producto is None:
                    flash("Elige un producto.", "danger")
                else:
                    pregunta = _pregunta_precio(producto)
            elif not texto_libre:
                flash("Escribe tu pregunta.", "danger")
            else:
                pregunta = texto_libre

            if pregunta:
                try:
                    respuesta = consultar_ia(INSTRUCCIONES_IA, pregunta)
                except IANoConfigurada as e:
                    aviso = str(e)
                except Exception as e:  # error de red, clave inválida, etc.
                    flash(f"No se pudo consultar la IA: {e}", "danger")

        return self.render_template(
            "asistente_ia.html",
            productos=productos,
            modo=modo,
            producto_id=producto_id,
            texto_libre=texto_libre,
            pregunta=pregunta,
            respuesta=respuesta,
            aviso=aviso,
            ia_lista=ia_configurada(),
        )
