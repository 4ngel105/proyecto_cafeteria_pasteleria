"""Página de inicio con el resumen del día."""
import datetime

from flask import g, redirect
from flask_appbuilder import IndexView, expose
from sqlalchemy import func

from .extensions import db
from .models import Cliente, DetalleVenta, Producto, Venta


def _resumen_ventas(desde, hasta):
    """Cantidad de ventas y total en Bs entre dos fechas."""
    cantidad = (
        db.session.query(func.count(Venta.id))
        .filter(Venta.fecha >= desde, Venta.fecha < hasta)
        .scalar()
    )
    total = (
        db.session.query(
            func.coalesce(
                func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario), 0
            )
        )
        .join(Venta)
        .filter(Venta.fecha >= desde, Venta.fecha < hasta)
        .scalar()
    )
    return cantidad, total


class InicioView(IndexView):
    index_template = "inicio.html"

    @expose("/")
    def index(self):
        if not g.user or not g.user.is_authenticated:
            return redirect(self.appbuilder.get_url_for_login)

        hoy = datetime.date.today()
        inicio_hoy = datetime.datetime.combine(hoy, datetime.time.min)
        manana = inicio_hoy + datetime.timedelta(days=1)
        inicio_mes = inicio_hoy.replace(day=1)

        ventas_hoy, total_hoy = _resumen_ventas(inicio_hoy, manana)
        ventas_mes, total_mes = _resumen_ventas(inicio_mes, manana)

        productos = (
            db.session.query(Producto).filter(Producto.activo.is_(True)).all()
        )
        bajo_costo = [p for p in productos if p.receta and p.precio_venta < p.costo()]
        sin_receta = [p for p in productos if not p.receta]

        ultimas_ventas = (
            db.session.query(Venta).order_by(Venta.fecha.desc()).limit(5).all()
        )

        return self.render_template(
            self.index_template,
            hoy=hoy,
            ventas_hoy=ventas_hoy,
            total_hoy=total_hoy,
            ventas_mes=ventas_mes,
            total_mes=total_mes,
            productos_activos=len(productos),
            clientes=db.session.query(func.count(Cliente.id)).scalar(),
            bajo_costo=bajo_costo,
            sin_receta=sin_receta,
            ultimas_ventas=ultimas_ventas,
        )
