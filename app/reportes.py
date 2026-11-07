"""Reportes: consultas reales a la base de datos con filtros."""
import datetime
from decimal import Decimal

from flask import flash, request
from flask_appbuilder import BaseView, expose, has_access
from sqlalchemy import func

from .extensions import db
from .models import Categoria, DetalleVenta, Producto, Venta
from .pantallas import METODOS_PAGO

# Importe de cada línea vendida: cantidad x precio al momento de la venta
IMPORTE = DetalleVenta.cantidad * DetalleVenta.precio_unitario


def _leer_fechas():
    """Lee el rango de fechas del filtro. Por defecto: el mes actual."""
    hoy = datetime.date.today()
    try:
        desde = datetime.date.fromisoformat(request.args.get("desde", ""))
    except ValueError:
        desde = hoy.replace(day=1)
    try:
        hasta = datetime.date.fromisoformat(request.args.get("hasta", ""))
    except ValueError:
        hasta = hoy
    if desde > hasta:
        flash("La fecha 'desde' no puede ser mayor que 'hasta'. Se invirtieron.", "warning")
        desde, hasta = hasta, desde
    return desde, hasta


def _filtrar_fechas(consulta, desde, hasta):
    """Ventas entre desde y hasta (ambos días incluidos)."""
    inicio = datetime.datetime.combine(desde, datetime.time.min)
    fin = datetime.datetime.combine(hasta + datetime.timedelta(days=1), datetime.time.min)
    return consulta.filter(Venta.fecha >= inicio, Venta.fecha < fin)


def _ventas_por_producto(desde, hasta, categoria_id):
    """Unidades vendidas e ingresos de cada producto en el rango."""
    consulta = (
        db.session.query(
            Producto.id,
            Producto.nombre,
            Categoria.nombre.label("categoria"),
            func.sum(DetalleVenta.cantidad).label("unidades"),
            func.sum(IMPORTE).label("ingresos"),
        )
        .select_from(DetalleVenta)
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .join(Producto, DetalleVenta.producto_id == Producto.id)
        .join(Categoria, Producto.categoria_id == Categoria.id)
    )
    consulta = _filtrar_fechas(consulta, desde, hasta)
    if categoria_id:
        consulta = consulta.filter(Producto.categoria_id == categoria_id)
    return consulta.group_by(Producto.id, Producto.nombre, Categoria.nombre).all()


def _categorias():
    return db.session.query(Categoria).order_by(Categoria.nombre).all()


class ReporteVentasView(BaseView):
    """Reporte 1: ventas por período, con filtro de fechas y método de pago."""

    route_base = "/reportes/ventas"
    default_view = "reporte"

    @expose("/")
    @has_access
    def reporte(self):
        desde, hasta = _leer_fechas()
        metodo = request.args.get("metodo", "")
        if metodo not in METODOS_PAGO:
            metodo = ""

        def filtrar(consulta):
            consulta = _filtrar_fechas(consulta, desde, hasta)
            return consulta.filter(Venta.metodo_pago == metodo) if metodo else consulta

        dia = func.date(Venta.fecha)
        por_dia = filtrar(
            db.session.query(
                dia.label("dia"),
                func.count(func.distinct(Venta.id)).label("ventas"),
                func.sum(IMPORTE).label("total"),
            ).join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        ).group_by(dia).order_by(dia).all()

        por_metodo = filtrar(
            db.session.query(
                Venta.metodo_pago,
                func.count(func.distinct(Venta.id)).label("ventas"),
                func.sum(IMPORTE).label("total"),
            ).join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        ).group_by(Venta.metodo_pago).order_by(func.sum(IMPORTE).desc()).all()

        ventas = filtrar(db.session.query(Venta)).order_by(Venta.fecha.desc()).all()

        total = sum((Decimal(d.total or 0) for d in por_dia), Decimal("0"))
        cantidad = len(ventas)
        return self.render_template(
            "reporte_ventas.html",
            desde=desde,
            hasta=hasta,
            metodo=metodo,
            metodos=METODOS_PAGO,
            por_dia=por_dia,
            por_metodo=por_metodo,
            ventas=ventas,
            total=total,
            cantidad=cantidad,
            promedio=(total / cantidad).quantize(Decimal("0.01")) if cantidad else Decimal("0"),
        )


class ReporteProductosView(BaseView):
    """Reporte 2: productos más vendidos, con filtro de fechas y categoría."""

    route_base = "/reportes/productos"
    default_view = "reporte"

    @expose("/")
    @has_access
    def reporte(self):
        desde, hasta = _leer_fechas()
        categoria_id = request.args.get("categoria", type=int)
        filas = sorted(
            _ventas_por_producto(desde, hasta, categoria_id),
            key=lambda f: (f.unidades, f.ingresos),
            reverse=True,
        )
        total_unidades = sum(f.unidades for f in filas)
        total_ingresos = sum((Decimal(f.ingresos) for f in filas), Decimal("0"))
        return self.render_template(
            "reporte_productos.html",
            desde=desde,
            hasta=hasta,
            categoria_id=categoria_id,
            categorias=_categorias(),
            filas=filas,
            total_unidades=total_unidades,
            total_ingresos=total_ingresos,
            max_unidades=max((f.unidades for f in filas), default=0),
        )


class ReporteGananciaView(BaseView):
    """Reporte 3: ganancia por producto (ingresos - costo de la receta)."""

    route_base = "/reportes/ganancia"
    default_view = "reporte"

    @expose("/")
    @has_access
    def reporte(self):
        desde, hasta = _leer_fechas()
        categoria_id = request.args.get("categoria", type=int)
        filas = []
        for f in _ventas_por_producto(desde, hasta, categoria_id):
            producto = db.session.get(Producto, f.id)
            ingresos = Decimal(f.ingresos)
            costo = (producto.costo() * f.unidades).quantize(Decimal("0.01"))
            ganancia = ingresos - costo
            filas.append(
                {
                    "id": f.id,
                    "nombre": f.nombre,
                    "categoria": f.categoria,
                    "unidades": f.unidades,
                    "costo_unitario": producto.costo(),
                    "sin_receta": not producto.receta,
                    "ingresos": ingresos,
                    "costo": costo,
                    "ganancia": ganancia,
                    "margen": (ganancia * 100 / ingresos).quantize(Decimal("0.1"))
                    if ingresos
                    else Decimal("0"),
                }
            )
        filas.sort(key=lambda f: f["ganancia"], reverse=True)
        total_ingresos = sum((f["ingresos"] for f in filas), Decimal("0"))
        total_costo = sum((f["costo"] for f in filas), Decimal("0"))
        total_ganancia = total_ingresos - total_costo
        return self.render_template(
            "reporte_ganancia.html",
            desde=desde,
            hasta=hasta,
            categoria_id=categoria_id,
            categorias=_categorias(),
            filas=filas,
            total_ingresos=total_ingresos,
            total_costo=total_costo,
            total_ganancia=total_ganancia,
            margen_total=(total_ganancia * 100 / total_ingresos).quantize(Decimal("0.1"))
            if total_ingresos
            else Decimal("0"),
        )
