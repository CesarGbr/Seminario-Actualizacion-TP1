from __future__ import annotations

import abc
from datetime import date
from decimal import Decimal
from typing import Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from price_manager.database.connection import ConexionDB
from price_manager.entities.entities import (
    Categoria,
    CotizacionDolar,
    Moneda,
    Precio,
    Producto,
    Proveedor,
    Stock,
    TipoCotizacion,
)
from price_manager.models.models import (
    CategoriaModel,
    CotizacionDolarModel,
    MonedaModel,
    PrecioModel,
    ProductoModel,
    ProveedorModel,
    StockModel,
    TipoCotizacionModel,
    crear_tablas,
)

T = TypeVar("T")

_CONEXION_DEFAULT = ConexionDB()
crear_tablas(_CONEXION_DEFAULT.engine)


def _normalizar_codigo(value: str) -> str:
    return value.strip().upper()


def _precio_a_entidad(model: PrecioModel) -> Precio:
    return Precio(
        id=model.id,
        valor=float(model.valor),
        moneda=model.moneda.nombre,
        fecha=model.fecha_actualizacion,
    )


def _categoria_a_entidad(model: CategoriaModel) -> Categoria:
    return Categoria(id=model.id, nombre=model.nombre)


def _proveedor_a_entidad(model: ProveedorModel) -> Proveedor:
    return Proveedor(
        id=model.id,
        nombre=model.nombre_legal,
        contacto=model.contacto,
    )


def _tipo_cotizacion_a_entidad(model: TipoCotizacionModel) -> TipoCotizacion:
    return TipoCotizacion(id=model.id, nombre=model.nombre)


def _cotizacion_a_entidad(model: CotizacionDolarModel) -> CotizacionDolar:
    return CotizacionDolar(
        id=model.id,
        valor=float(model.valor),
        fecha=model.fecha,
        tipo=model.tipo_cotizacion.nombre,
    )


def _producto_a_entidad(model: ProductoModel) -> Producto:
    return Producto(
        id=model.id,
        nombre=model.nombre,
        descripcion=model.descripcion,
        precio=_precio_a_entidad(model.precio),
        categoria=_categoria_a_entidad(model.categoria),
        proveedor=_proveedor_a_entidad(model.proveedor),
    )


def _stock_a_entidad(model: StockModel) -> Stock:
    return Stock(
        id=model.id,
        producto=_producto_a_entidad(model.producto),
        almacen=model.almacen,
        cantidad=model.cantidad,
    )


def _valor_decimal(value: float) -> Decimal:
    return Decimal(str(value))


def _resolver_moneda_id(sesion: Session, codigo: str) -> int:
    codigo_normalizado = _normalizar_codigo(codigo)
    moneda = sesion.scalar(
        select(MonedaModel).where(MonedaModel.nombre == codigo_normalizado)
    )
    if moneda is not None:
        return moneda.id

    moneda = MonedaModel(nombre=codigo_normalizado)
    sesion.add(moneda)
    sesion.flush()
    return moneda.id


def _resolver_tipo_cotizacion_id(sesion: Session, nombre: str) -> int:
    nombre_normalizado = _normalizar_codigo(nombre)
    tipo = sesion.scalar(
        select(TipoCotizacionModel).where(TipoCotizacionModel.nombre == nombre_normalizado)
    )
    if tipo is not None:
        return tipo.id

    tipo = TipoCotizacionModel(nombre=nombre_normalizado)
    sesion.add(tipo)
    sesion.flush()
    return tipo.id


def _producto_options():
    return (
        joinedload(ProductoModel.precio).joinedload(PrecioModel.moneda),
        joinedload(ProductoModel.categoria),
        joinedload(ProductoModel.proveedor),
    )


def _stock_options():
    return (
        joinedload(StockModel.producto)
        .joinedload(ProductoModel.precio)
        .joinedload(PrecioModel.moneda),
        joinedload(StockModel.producto).joinedload(ProductoModel.categoria),
        joinedload(StockModel.producto).joinedload(ProductoModel.proveedor),
    )


class IRepositorio(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        pass

    @abc.abstractmethod
    def leer_por_id(self, entidad_id: int) -> T | None:
        pass

    @abc.abstractmethod
    def leer_todos(self) -> list[T]:
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        pass

    @abc.abstractmethod
    def eliminar(self, entidad_id: int) -> bool:
        pass


class IRepositorioStock(abc.ABC):
    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        pass

    @abc.abstractmethod
    def leer_por_producto(self, producto_id: int) -> Stock | None:
        pass

    @abc.abstractmethod
    def leer_todos(self) -> list[Stock]:
        pass

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        pass

    @abc.abstractmethod
    def eliminar(self, producto_id: int) -> bool:
        pass


class IRepositorioCotizacionDolar(abc.ABC):
    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        pass

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self,
        tipo: str,
        fecha_cotizacion: date,
    ) -> CotizacionDolar | None:
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
        pass

    @abc.abstractmethod
    def leer_todos(self) -> list[CotizacionDolar]:
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        pass

    @abc.abstractmethod
    def eliminar(self, cotizacion_id: int) -> bool:
        pass


class _RepositorioSQLBase(IRepositorio[T], Generic[T]):
    model_cls: type

    def __init__(self, conexion: ConexionDB | None = None) -> None:
        self._conexion = conexion or _CONEXION_DEFAULT

    def _to_entity(self, model) -> T:
        raise NotImplementedError

    def _as_values(self, entidad: T) -> dict[str, object]:
        raise NotImplementedError

    def crear(self, entidad: T) -> T:
        values = self._as_values(entidad)
        entidad_id = values["id"]
        try:
            with self._conexion.transaccion() as sesion:
                if sesion.get(self.model_cls, entidad_id) is not None:
                    raise ValueError(f"Ya existe un registro con id {entidad_id}")
                model = self.model_cls(**values)
                sesion.add(model)
                sesion.flush()
                return self._to_entity(model)
        except IntegrityError as exc:
            raise ValueError("No se pudo crear el registro por restriccion de datos") from exc

    def leer_por_id(self, entidad_id: int) -> T | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = sesion.get(self.model_cls, entidad_id)
            if model is None:
                return None
            return self._to_entity(model)
        finally:
            sesion.close()

    def leer_todos(self) -> list[T]:
        sesion = self._conexion.crear_sesion()
        try:
            stmt = select(self.model_cls).order_by(self.model_cls.id)
            modelos = sesion.scalars(stmt).all()
            return [self._to_entity(item) for item in modelos]
        finally:
            sesion.close()

    def actualizar(self, entidad: T) -> T:
        values = self._as_values(entidad)
        entidad_id = values["id"]
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(self.model_cls, entidad_id)
                if model is None:
                    raise ValueError(f"No existe un registro con id {entidad_id}")
                for key, value in values.items():
                    setattr(model, key, value)
                sesion.flush()
                return self._to_entity(model)
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo actualizar el registro por restriccion de datos"
            ) from exc

    def eliminar(self, entidad_id: int) -> bool:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(self.model_cls, entidad_id)
                if model is None:
                    return False
                sesion.delete(model)
                return True
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo eliminar el registro porque esta en uso"
            ) from exc


class RepositorioCategoria(_RepositorioSQLBase[Categoria]):
    model_cls = CategoriaModel

    def _to_entity(self, model: CategoriaModel) -> Categoria:
        return _categoria_a_entidad(model)

    def _as_values(self, entidad: Categoria) -> dict[str, object]:
        return {"id": entidad.id, "nombre": entidad.nombre}


class RepositorioProveedor(_RepositorioSQLBase[Proveedor]):
    model_cls = ProveedorModel

    def _to_entity(self, model: ProveedorModel) -> Proveedor:
        return _proveedor_a_entidad(model)

    def _as_values(self, entidad: Proveedor) -> dict[str, object]:
        return {
            "id": entidad.id,
            "nombre_legal": entidad.nombre_legal,
            "contacto": entidad.contacto,
        }


class RepositorioMoneda(_RepositorioSQLBase[Moneda]):
    model_cls = MonedaModel

    def _to_entity(self, model: MonedaModel) -> Moneda:
        return Moneda(id=model.id, nombre=model.nombre)

    def _as_values(self, entidad: Moneda) -> dict[str, object]:
        return {"id": entidad.id, "nombre": _normalizar_codigo(entidad.nombre)}


class RepositorioTipoCotizacion(_RepositorioSQLBase[TipoCotizacion]):
    model_cls = TipoCotizacionModel

    def _to_entity(self, model: TipoCotizacionModel) -> TipoCotizacion:
        return _tipo_cotizacion_a_entidad(model)

    def _as_values(self, entidad: TipoCotizacion) -> dict[str, object]:
        return {"id": entidad.id, "nombre": _normalizar_codigo(entidad.nombre)}


class RepositorioPrecio(IRepositorio[Precio]):
    def __init__(self, conexion: ConexionDB | None = None) -> None:
        self._conexion = conexion or _CONEXION_DEFAULT

    def crear(self, entidad: Precio) -> Precio:
        try:
            with self._conexion.transaccion() as sesion:
                if sesion.get(PrecioModel, entidad.id) is not None:
                    raise ValueError(f"Ya existe un registro con id {entidad.id}")
                moneda_id = _resolver_moneda_id(sesion, entidad.moneda)
                model = PrecioModel(
                    id=entidad.id,
                    valor=_valor_decimal(entidad.valor),
                    moneda_id=moneda_id,
                    fecha_actualizacion=entidad.fecha_actualizacion,
                )
                sesion.add(model)
                sesion.flush()
                model = sesion.scalar(
                    select(PrecioModel)
                    .options(joinedload(PrecioModel.moneda))
                    .where(PrecioModel.id == entidad.id)
                )
                return _precio_a_entidad(model)
        except IntegrityError as exc:
            raise ValueError("No se pudo crear el precio por restriccion de datos") from exc

    def leer_por_id(self, entidad_id: int) -> Precio | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = sesion.scalar(
                select(PrecioModel)
                .options(joinedload(PrecioModel.moneda))
                .where(PrecioModel.id == entidad_id)
            )
            if model is None:
                return None
            return _precio_a_entidad(model)
        finally:
            sesion.close()

    def leer_todos(self) -> list[Precio]:
        sesion = self._conexion.crear_sesion()
        try:
            modelos = sesion.scalars(
                select(PrecioModel)
                .options(joinedload(PrecioModel.moneda))
                .order_by(PrecioModel.id)
            ).all()
            return [_precio_a_entidad(item) for item in modelos]
        finally:
            sesion.close()

    def actualizar(self, entidad: Precio) -> Precio:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(PrecioModel, entidad.id)
                if model is None:
                    raise ValueError(f"No existe un registro con id {entidad.id}")
                model.valor = _valor_decimal(entidad.valor)
                model.moneda_id = _resolver_moneda_id(sesion, entidad.moneda)
                model.fecha_actualizacion = entidad.fecha_actualizacion
                sesion.flush()
                model = sesion.scalar(
                    select(PrecioModel)
                    .options(joinedload(PrecioModel.moneda))
                    .where(PrecioModel.id == entidad.id)
                )
                return _precio_a_entidad(model)
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo actualizar el precio por restriccion de datos"
            ) from exc

    def eliminar(self, entidad_id: int) -> bool:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(PrecioModel, entidad_id)
                if model is None:
                    return False
                sesion.delete(model)
                return True
        except IntegrityError as exc:
            raise ValueError("No se puede eliminar el precio porque esta en uso") from exc


class RepositorioProducto(IRepositorio[Producto]):
    def __init__(self, conexion: ConexionDB | None = None) -> None:
        self._conexion = conexion or _CONEXION_DEFAULT

    def _query_by_id(self, sesion: Session, producto_id: int) -> ProductoModel | None:
        return sesion.scalar(
            select(ProductoModel)
            .options(*_producto_options())
            .where(ProductoModel.id == producto_id)
        )

    def crear(self, entidad: Producto) -> Producto:
        try:
            with self._conexion.transaccion() as sesion:
                if sesion.get(ProductoModel, entidad.id) is not None:
                    raise ValueError(f"Ya existe un registro con id {entidad.id}")
                model = ProductoModel(
                    id=entidad.id,
                    nombre=entidad.nombre,
                    descripcion=entidad.descripcion,
                    precio_id=entidad.precio.id,
                    categoria_id=entidad.categoria.id,
                    proveedor_id=entidad.proveedor.id,
                )
                sesion.add(model)
                sesion.flush()
                cargado = self._query_by_id(sesion, entidad.id)
                return _producto_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError("No se pudo crear el producto por datos invalidos o faltantes") from exc

    def leer_por_id(self, entidad_id: int) -> Producto | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = self._query_by_id(sesion, entidad_id)
            if model is None:
                return None
            return _producto_a_entidad(model)
        finally:
            sesion.close()

    def leer_todos(self) -> list[Producto]:
        sesion = self._conexion.crear_sesion()
        try:
            modelos = sesion.scalars(
                select(ProductoModel)
                .options(*_producto_options())
                .order_by(ProductoModel.id)
            ).all()
            return [_producto_a_entidad(item) for item in modelos]
        finally:
            sesion.close()

    def actualizar(self, entidad: Producto) -> Producto:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(ProductoModel, entidad.id)
                if model is None:
                    raise ValueError(f"No existe un registro con id {entidad.id}")
                model.nombre = entidad.nombre
                model.descripcion = entidad.descripcion
                model.precio_id = entidad.precio.id
                model.categoria_id = entidad.categoria.id
                model.proveedor_id = entidad.proveedor.id
                sesion.flush()
                cargado = self._query_by_id(sesion, entidad.id)
                return _producto_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo actualizar el producto por datos invalidos o faltantes"
            ) from exc

    def eliminar(self, entidad_id: int) -> bool:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(ProductoModel, entidad_id)
                if model is None:
                    return False
                sesion.execute(
                    delete(StockModel).where(StockModel.producto_id == entidad_id)
                )
                sesion.delete(model)
                return True
        except IntegrityError as exc:
            raise ValueError("No se pudo eliminar el producto porque esta en uso") from exc


class RepositorioStock(IRepositorioStock):
    def __init__(self, conexion: ConexionDB | None = None) -> None:
        self._conexion = conexion or _CONEXION_DEFAULT

    def _query_by_id(self, sesion: Session, stock_id: int) -> StockModel | None:
        return sesion.scalar(
            select(StockModel)
            .options(*_stock_options())
            .where(StockModel.id == stock_id)
        )

    def _query_by_producto(
        self, sesion: Session, producto_id: int
    ) -> StockModel | None:
        return sesion.scalar(
            select(StockModel)
            .options(*_stock_options())
            .where(StockModel.producto_id == producto_id)
        )

    def crear(self, stock: Stock) -> Stock:
        try:
            with self._conexion.transaccion() as sesion:
                if sesion.get(StockModel, stock.id) is not None:
                    raise ValueError(f"Ya existe stock con id {stock.id}")
                if self._query_by_producto(sesion, stock.producto.id) is not None:
                    raise ValueError(
                        f"Ya existe stock para producto {stock.producto.id}"
                    )
                model = StockModel(
                    id=stock.id,
                    producto_id=stock.producto.id,
                    almacen=stock.almacen,
                    cantidad=stock.cantidad,
                )
                sesion.add(model)
                sesion.flush()
                cargado = self._query_by_id(sesion, stock.id)
                return _stock_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError("No se pudo crear stock por datos invalidos o faltantes") from exc

    def leer_por_producto(self, producto_id: int) -> Stock | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = self._query_by_producto(sesion, producto_id)
            if model is None:
                return None
            return _stock_a_entidad(model)
        finally:
            sesion.close()

    def leer_por_id(self, stock_id: int) -> Stock | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = self._query_by_id(sesion, stock_id)
            if model is None:
                return None
            return _stock_a_entidad(model)
        finally:
            sesion.close()

    def leer_todos(self) -> list[Stock]:
        sesion = self._conexion.crear_sesion()
        try:
            modelos = sesion.scalars(
                select(StockModel)
                .options(*_stock_options())
                .order_by(StockModel.id)
            ).all()
            return [_stock_a_entidad(item) for item in modelos]
        finally:
            sesion.close()

    def actualizar(self, stock: Stock) -> Stock:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(StockModel, stock.id)
                if model is None:
                    raise ValueError(f"No existe stock con id {stock.id}")

                if stock.producto.id != model.producto_id:
                    existe_otro = self._query_by_producto(sesion, stock.producto.id)
                    if existe_otro is not None and existe_otro.id != stock.id:
                        raise ValueError(
                            f"Ya existe stock para producto {stock.producto.id}"
                        )

                model.producto_id = stock.producto.id
                model.almacen = stock.almacen
                model.cantidad = stock.cantidad
                sesion.flush()
                cargado = self._query_by_id(sesion, stock.id)
                return _stock_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError("No se pudo actualizar stock por datos invalidos") from exc

    def eliminar(self, producto_id: int) -> bool:
        with self._conexion.transaccion() as sesion:
            model = sesion.scalar(
                select(StockModel).where(StockModel.producto_id == producto_id)
            )
            if model is None:
                return False
            sesion.delete(model)
            return True

    def eliminar_por_id(self, stock_id: int) -> bool:
        with self._conexion.transaccion() as sesion:
            model = sesion.get(StockModel, stock_id)
            if model is None:
                return False
            sesion.delete(model)
            return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    def __init__(self, conexion: ConexionDB | None = None) -> None:
        self._conexion = conexion or _CONEXION_DEFAULT

    def _query_by_id(
        self, sesion: Session, cotizacion_id: int
    ) -> CotizacionDolarModel | None:
        return sesion.scalar(
            select(CotizacionDolarModel)
            .options(joinedload(CotizacionDolarModel.tipo_cotizacion))
            .where(CotizacionDolarModel.id == cotizacion_id)
        )

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        try:
            with self._conexion.transaccion() as sesion:
                if sesion.get(CotizacionDolarModel, cotizacion.id) is not None:
                    raise ValueError(
                        f"Ya existe cotizacion con id {cotizacion.id}"
                    )
                tipo_id = _resolver_tipo_cotizacion_id(sesion, cotizacion.tipo)
                existente = sesion.scalar(
                    select(CotizacionDolarModel).where(
                        CotizacionDolarModel.tipo_cotizacion_id == tipo_id,
                        CotizacionDolarModel.fecha == cotizacion.fecha,
                    )
                )
                if existente is not None:
                    raise ValueError("Ya existe una cotizacion para ese tipo y fecha")
                model = CotizacionDolarModel(
                    id=cotizacion.id,
                    valor=_valor_decimal(cotizacion.valor),
                    fecha=cotizacion.fecha,
                    tipo_cotizacion_id=tipo_id,
                )
                sesion.add(model)
                sesion.flush()
                cargado = self._query_by_id(sesion, cotizacion.id)
                return _cotizacion_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError("No se pudo crear la cotizacion por datos invalidos") from exc

    def leer_por_tipo_y_fecha(
        self,
        tipo: str,
        fecha_cotizacion: date,
    ) -> CotizacionDolar | None:
        sesion = self._conexion.crear_sesion()
        try:
            tipo_normalizado = _normalizar_codigo(tipo)
            model = sesion.scalar(
                select(CotizacionDolarModel)
                .join(CotizacionDolarModel.tipo_cotizacion)
                .options(joinedload(CotizacionDolarModel.tipo_cotizacion))
                .where(
                    TipoCotizacionModel.nombre == tipo_normalizado,
                    CotizacionDolarModel.fecha == fecha_cotizacion,
                )
            )
            if model is None:
                return None
            return _cotizacion_a_entidad(model)
        finally:
            sesion.close()

    def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
        sesion = self._conexion.crear_sesion()
        try:
            tipo_normalizado = _normalizar_codigo(tipo)
            modelos = sesion.scalars(
                select(CotizacionDolarModel)
                .join(CotizacionDolarModel.tipo_cotizacion)
                .options(joinedload(CotizacionDolarModel.tipo_cotizacion))
                .where(TipoCotizacionModel.nombre == tipo_normalizado)
                .order_by(CotizacionDolarModel.fecha, CotizacionDolarModel.id)
            ).all()
            return [_cotizacion_a_entidad(item) for item in modelos]
        finally:
            sesion.close()

    def leer_todos(self) -> list[CotizacionDolar]:
        sesion = self._conexion.crear_sesion()
        try:
            modelos = sesion.scalars(
                select(CotizacionDolarModel)
                .options(joinedload(CotizacionDolarModel.tipo_cotizacion))
                .order_by(CotizacionDolarModel.id)
            ).all()
            return [_cotizacion_a_entidad(item) for item in modelos]
        finally:
            sesion.close()

    def leer_por_id(self, cotizacion_id: int) -> CotizacionDolar | None:
        sesion = self._conexion.crear_sesion()
        try:
            model = self._query_by_id(sesion, cotizacion_id)
            if model is None:
                return None
            return _cotizacion_a_entidad(model)
        finally:
            sesion.close()

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        try:
            with self._conexion.transaccion() as sesion:
                model = sesion.get(CotizacionDolarModel, cotizacion.id)
                if model is None:
                    raise ValueError(
                        f"No existe cotizacion con id {cotizacion.id}"
                    )

                tipo_id = _resolver_tipo_cotizacion_id(sesion, cotizacion.tipo)
                existente = sesion.scalar(
                    select(CotizacionDolarModel).where(
                        CotizacionDolarModel.tipo_cotizacion_id == tipo_id,
                        CotizacionDolarModel.fecha == cotizacion.fecha,
                        CotizacionDolarModel.id != cotizacion.id,
                    )
                )
                if existente is not None:
                    raise ValueError("Ya existe una cotizacion para ese tipo y fecha")

                model.valor = _valor_decimal(cotizacion.valor)
                model.fecha = cotizacion.fecha
                model.tipo_cotizacion_id = tipo_id
                sesion.flush()
                cargado = self._query_by_id(sesion, cotizacion.id)
                return _cotizacion_a_entidad(cargado)
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo actualizar la cotizacion por datos invalidos"
            ) from exc

    def eliminar(self, cotizacion_id: int) -> bool:
        with self._conexion.transaccion() as sesion:
            model = sesion.get(CotizacionDolarModel, cotizacion_id)
            if model is None:
                return False
            sesion.delete(model)
            return True
