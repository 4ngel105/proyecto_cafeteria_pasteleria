import datetime
from decimal import Decimal

from flask_appbuilder import Model
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class Categoria(Model):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(250), nullable=True)
    activo = Column(Boolean, default=True)

    productos = relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return self.nombre


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
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    precio_venta = Column(Numeric(10, 2), default=0, nullable=False)
    # Porcentaje de ganancia que se suma al costo para sugerir el precio
    margen_ganancia = Column(Numeric(5, 2), default=50, nullable=False)
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="productos")
    receta = relationship(
        "Receta", back_populates="producto", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.nombre

    def costo(self):
        """Costo del producto: suma del costo de cada ingrediente de su receta."""
        total = sum((item.subtotal() for item in self.receta), Decimal("0"))
        return total.quantize(Decimal("0.01"))

    def precio_sugerido(self):
        """Costo + el porcentaje de ganancia del producto."""
        margen = Decimal(self.margen_ganancia or 0)
        precio = self.costo() * (1 + margen / 100)
        return precio.quantize(Decimal("0.01"))


class Ingrediente(Model):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    # Unidad en la que se compra y se mide: kg, g, l, ml, unidad...
    unidad_medida = Column(String(20), nullable=False)
    # Cuánto cuesta una unidad de medida (ej: 1 kg de café)
    costo_unitario = Column(Numeric(10, 2), default=0, nullable=False)
    activo = Column(Boolean, default=True)

    recetas = relationship("Receta", back_populates="ingrediente")

    def __repr__(self):
        return f"{self.nombre} ({self.unidad_medida})"


class Receta(Model):
    """Qué ingrediente y cuánto lleva cada producto."""

    __tablename__ = "recetas"
    __table_args__ = (
        UniqueConstraint("producto_id", "ingrediente_id", name="uq_receta"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), nullable=False)
    # Cantidad en la unidad de medida del ingrediente (ej: 0.018 kg)
    cantidad = Column(Numeric(10, 3), nullable=False)

    producto = relationship("Producto", back_populates="receta")
    ingrediente = relationship("Ingrediente", back_populates="recetas")

    def __repr__(self):
        return f"{self.producto} - {self.ingrediente}"

    def subtotal(self):
        """Costo de este ingrediente dentro del producto."""
        costo = Decimal(self.ingrediente.costo_unitario or 0)
        return (Decimal(self.cantidad or 0) * costo).quantize(Decimal("0.01"))
