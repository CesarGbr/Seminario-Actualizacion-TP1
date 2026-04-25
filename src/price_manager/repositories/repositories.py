from __future__ import annotations

import abc
from datetime import date
from typing import Generic, TypeVar

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

T = TypeVar("T")


class IRepositorio(abc.ABC, Generic[T]):
  """Contrato CRUD generico.

  Define que operaciones debe exponer un repositorio, sin imponer
  detalles de implementacion.
  """

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
  """Contrato de stock.

  Se separa del CRUD generico porque stock se consulta/elimina por
  producto y tiene reglas de unicidad por producto.
  """

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
  """Contrato de cotizaciones.

  Agrega operaciones de dominio que no estan en el CRUD base:
  busqueda por (tipo, fecha) e historico por tipo.
  """

  @abc.abstractmethod
  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    pass

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(self, tipo: str, fecha_cotizacion: date) -> CotizacionDolar | None:
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


class RepositorioBase(IRepositorio[T], Generic[T]):
  """Implementacion reusable del contrato CRUD."""

  def __init__(self) -> None:
    self._data: dict[int, T] = {}

  def crear(self, entidad: T) -> T:
    entidad_id = getattr(entidad, "id")
    if entidad_id in self._data:
      raise ValueError(f"Ya existe un registro con id {entidad_id}")
    self._data[entidad_id] = entidad
    return entidad

  def leer_por_id(self, entidad_id: int) -> T | None:
    return self._data.get(entidad_id)

  def leer_todos(self) -> list[T]:
    return list(self._data.values())

  def actualizar(self, entidad: T) -> T:
    entidad_id = getattr(entidad, "id")
    if entidad_id not in self._data:
      raise ValueError(f"No existe un registro con id {entidad_id}")
    self._data[entidad_id] = entidad
    return entidad

  def eliminar(self, entidad_id: int) -> bool:
    if entidad_id not in self._data:
      return False
    del self._data[entidad_id]
    return True


class RepositorioCategoria(RepositorioBase[Categoria]):
  pass


class RepositorioProveedor(RepositorioBase[Proveedor]):
  pass


class RepositorioPrecio(RepositorioBase[Precio]):
  pass


class RepositorioMoneda(RepositorioBase[Moneda]):
  pass


class RepositorioTipoCotizacion(RepositorioBase[TipoCotizacion]):
  pass


class RepositorioProducto(RepositorioBase[Producto]):
  pass


class RepositorioStock(IRepositorioStock):
  def __init__(self) -> None:
    self._by_id: dict[int, Stock] = {}
    self._by_producto_id: dict[int, int] = {}

  def crear(self, stock: Stock) -> Stock:
    if stock.id in self._by_id:
      raise ValueError(f"Ya existe stock con id {stock.id}")
    if stock.producto.id in self._by_producto_id:
      raise ValueError(f"Ya existe stock para producto {stock.producto.id}")
    self._by_id[stock.id] = stock
    self._by_producto_id[stock.producto.id] = stock.id
    return stock

  def leer_por_producto(self, producto_id: int) -> Stock | None:
    stock_id = self._by_producto_id.get(producto_id)
    if stock_id is None:
      return None
    return self._by_id.get(stock_id)

  def leer_por_id(self, stock_id: int) -> Stock | None:
    return self._by_id.get(stock_id)

  def leer_todos(self) -> list[Stock]:
    return list(self._by_id.values())

  def actualizar(self, stock: Stock) -> Stock:
    if stock.id not in self._by_id:
      raise ValueError(f"No existe stock con id {stock.id}")
    actual = self._by_id[stock.id]
    if stock.producto.id != actual.producto.id:
      if stock.producto.id in self._by_producto_id:
        raise ValueError(f"Ya existe stock para producto {stock.producto.id}")
      del self._by_producto_id[actual.producto.id]
      self._by_producto_id[stock.producto.id] = stock.id
    self._by_id[stock.id] = stock
    return stock

  def eliminar(self, producto_id: int) -> bool:
    stock_id = self._by_producto_id.get(producto_id)
    if stock_id is None:
      return False
    del self._by_producto_id[producto_id]
    del self._by_id[stock_id]
    return True

  def eliminar_por_id(self, stock_id: int) -> bool:
    stock = self._by_id.get(stock_id)
    if stock is None:
      return False
    del self._by_id[stock_id]
    del self._by_producto_id[stock.producto.id]
    return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
  def __init__(self) -> None:
    self._data: dict[int, CotizacionDolar] = {}

  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    if cotizacion.id in self._data:
      raise ValueError(f"Ya existe cotizacion con id {cotizacion.id}")
    if self.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha) is not None:
      raise ValueError("Ya existe una cotizacion para ese tipo y fecha")
    self._data[cotizacion.id] = cotizacion
    return cotizacion

  def leer_por_tipo_y_fecha(self, tipo: str, fecha_cotizacion: date) -> CotizacionDolar | None:
    tipo_normalizado = tipo.strip().upper()
    for item in self._data.values():
      if item.tipo == tipo_normalizado and item.fecha == fecha_cotizacion:
        return item
    return None

  def leer_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
    tipo_normalizado = tipo.strip().upper()
    resultado = [item for item in self._data.values() if item.tipo == tipo_normalizado]
    return sorted(resultado, key=lambda x: x.fecha)

  def leer_todos(self) -> list[CotizacionDolar]:
    return list(self._data.values())

  def leer_por_id(self, cotizacion_id: int) -> CotizacionDolar | None:
    return self._data.get(cotizacion_id)

  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    if cotizacion.id not in self._data:
      raise ValueError(f"No existe cotizacion con id {cotizacion.id}")
    existente = self.leer_por_tipo_y_fecha(cotizacion.tipo, cotizacion.fecha)
    if existente is not None and existente.id != cotizacion.id:
      raise ValueError("Ya existe una cotizacion para ese tipo y fecha")
    self._data[cotizacion.id] = cotizacion
    return cotizacion

  def eliminar(self, cotizacion_id: int) -> bool:
    if cotizacion_id not in self._data:
      return False
    del self._data[cotizacion_id]
    return True
