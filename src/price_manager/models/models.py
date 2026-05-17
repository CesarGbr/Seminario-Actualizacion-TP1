from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa para los modelos ORM."""


class CategoriaModel(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    productos: Mapped[list["ProductoModel"]] = relationship(
        back_populates="categoria"
    )


class ProveedorModel(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_legal: Mapped[str] = mapped_column(String(150), nullable=False)
    contacto: Mapped[str] = mapped_column(String(150), nullable=False)

    productos: Mapped[list["ProductoModel"]] = relationship(
        back_populates="proveedor"
    )


class MonedaModel(Base):
    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)

    precios: Mapped[list["PrecioModel"]] = relationship(back_populates="moneda")


class TipoCotizacionModel(Base):
    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    cotizaciones: Mapped[list["CotizacionDolarModel"]] = relationship(
        back_populates="tipo_cotizacion"
    )


class PrecioModel(Base):
    __tablename__ = "precios"
    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_precios_valor_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id"),
        nullable=False,
    )
    fecha_actualizacion: Mapped[date] = mapped_column(Date, nullable=False)

    moneda: Mapped["MonedaModel"] = relationship(back_populates="precios")
    producto: Mapped["ProductoModel"] = relationship(
        back_populates="precio",
        uselist=False,
    )


class CotizacionDolarModel(Base):
    __tablename__ = "cotizaciones_dolar"
    __table_args__ = (
        UniqueConstraint(
            "tipo_cotizacion_id",
            "fecha",
            name="uq_cotizaciones_tipo_fecha",
        ),
        CheckConstraint("valor > 0", name="ck_cotizaciones_valor_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo_cotizacion_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id"),
        nullable=False,
    )

    tipo_cotizacion: Mapped["TipoCotizacionModel"] = relationship(
        back_populates="cotizaciones"
    )


class ProductoModel(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    precio_id: Mapped[int] = mapped_column(
        ForeignKey("precios.id"),
        nullable=False,
        unique=True,
    )
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id"),
        nullable=False,
    )
    proveedor_id: Mapped[int] = mapped_column(
        ForeignKey("proveedores.id"),
        nullable=False,
    )

    precio: Mapped["PrecioModel"] = relationship(
        back_populates="producto",
        uselist=False,
    )
    categoria: Mapped["CategoriaModel"] = relationship(back_populates="productos")
    proveedor: Mapped["ProveedorModel"] = relationship(back_populates="productos")
    stock: Mapped["StockModel"] = relationship(
        back_populates="producto",
        uselist=False,
    )


class StockModel(Base):
    __tablename__ = "stock"
    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_stock_cantidad_no_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"),
        nullable=False,
        unique=True,
    )
    almacen: Mapped[str] = mapped_column(String(120), nullable=False)
    cantidad: Mapped[int] = mapped_column(nullable=False)

    producto: Mapped["ProductoModel"] = relationship(back_populates="stock")


def crear_tablas(engine: Engine) -> None:
    """Crea todas las tablas declaradas en este modulo."""
    Base.metadata.create_all(bind=engine)
