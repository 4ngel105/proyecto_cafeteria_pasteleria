import datetime

from flask_appbuilder import Model
from sqlalchemy import Boolean, Column, Date, Integer, Numeric, String, Text


class Cliente(Model):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    ci_nit = Column(String(20), unique=True, nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    fecha_registro = Column(Date, default=datetime.date.today, nullable=False)
    activo = Column(Boolean, default=True)

    def __repr__(self):
        return f"{self.nombre} {self.apellido}"


class Producto(Model):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    precio_venta = Column(Numeric(10, 2), default=0, nullable=False)
    activo = Column(Boolean, default=True)

    def __repr__(self):
        return self.nombre
