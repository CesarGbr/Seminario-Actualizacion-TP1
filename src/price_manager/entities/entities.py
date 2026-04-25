from __future__ import annotations

from datetime import date
import unicodedata


def _normalize_tipo_nombre(value: str) -> str:
  base = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
  normalizado = " ".join(base.strip().upper().split())
  if normalizado.startswith("DOLAR "):
    normalizado = normalizado.replace("DOLAR ", "", 1)
  return normalizado


class Categoria:
  """Representa el rubro de un producto."""

  def __init__(self, categoria_id: int | None = None, nombre: str = "", id: int | None = None) -> None:
    resolved_id = categoria_id if categoria_id is not None else id
    if resolved_id is None:
      raise ValueError("Debe informar id de categoria")
    self.id = resolved_id
    self.nombre = nombre

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de categoria debe ser mayor a cero")
    self._id = value

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El nombre de categoria no puede estar vacio")
    self._nombre = value.strip()


class Proveedor:
  """Representa un proveedor de mercaderia."""

  def __init__(
    self,
    proveedor_id: int | None = None,
    nombre_legal: str | None = None,
    contacto: str = "",
    id: int | None = None,
    nombre: str | None = None,
  ) -> None:
    resolved_id = proveedor_id if proveedor_id is not None else id
    if resolved_id is None:
      raise ValueError("Debe informar id de proveedor")
    self.id = resolved_id
    self.nombre_legal = nombre_legal if nombre_legal is not None else (nombre or "")
    self.contacto = contacto

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de proveedor debe ser mayor a cero")
    self._id = value

  @property
  def nombre_legal(self) -> str:
    return self._nombre_legal

  @nombre_legal.setter
  def nombre_legal(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El nombre legal no puede estar vacio")
    self._nombre_legal = value.strip()

  @property
  def contacto(self) -> str:
    return self._contacto

  @contacto.setter
  def contacto(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El contacto no puede estar vacio")
    self._contacto = value.strip()


class Moneda:
  """Entidad de moneda para compatibilidad con notebook."""

  def __init__(self, moneda_id: int | None = None, nombre: str = "", id: int | None = None) -> None:
    resolved_id = moneda_id if moneda_id is not None else id
    if resolved_id is None:
      raise ValueError("Debe informar id de moneda")
    self.id = resolved_id
    self.nombre = nombre

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de moneda debe ser mayor a cero")
    self._id = value

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El nombre de moneda no puede estar vacio")
    self._nombre = value.strip()


class TipoCotizacion:
  """Entidad de tipo de cotizacion para compatibilidad con notebook."""

  def __init__(self, tipo_cotizacion_id: int | None = None, nombre: str = "", id: int | None = None) -> None:
    resolved_id = tipo_cotizacion_id if tipo_cotizacion_id is not None else id
    if resolved_id is None:
      raise ValueError("Debe informar id de tipo cotizacion")
    self.id = resolved_id
    self.nombre = nombre

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de tipo cotizacion debe ser mayor a cero")
    self._id = value

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, value: str) -> None:
    normalizado = _normalize_tipo_nombre(value)
    if normalizado not in CotizacionDolar.TIPOS_VALIDOS:
      raise ValueError(f"Tipo de cotizacion invalido: {value}")
    self._nombre = value.strip()


class Precio:
  """Representa el valor monetario de un producto."""

  _next_id = 1

  def __init__(
    self,
    valor: float,
    moneda: str | Moneda,
    precio_id: int | None = None,
    fecha_actualizacion: date | None = None,
    id: int | None = None,
    fecha: date | None = None,
  ) -> None:
    resolved_id = precio_id if precio_id is not None else id
    if resolved_id is None:
      resolved_id = Precio._next_id
      Precio._next_id += 1
    self.id = resolved_id
    self.valor = valor
    self.moneda = moneda
    self.fecha_actualizacion = fecha_actualizacion or fecha or date.today()

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de precio debe ser mayor a cero")
    self._id = value

  @property
  def valor(self) -> float:
    return self._valor

  @valor.setter
  def valor(self, value: float) -> None:
    if value < 0:
      raise ValueError("El valor de precio no puede ser negativo")
    self._valor = float(value)

  @property
  def moneda(self) -> str:
    return self._moneda

  @moneda.setter
  def moneda(self, value: str | Moneda) -> None:
    if isinstance(value, Moneda):
      codigo = value.nombre.strip().upper()[:3]
    else:
      codigo = value.strip().upper()
    if not codigo:
      raise ValueError("La moneda no puede estar vacia")
    self._moneda = codigo

  @property
  def fecha_actualizacion(self) -> date:
    return self._fecha_actualizacion

  @fecha_actualizacion.setter
  def fecha_actualizacion(self, value: date) -> None:
    self._fecha_actualizacion = value


class CotizacionDolar:
  """Representa una cotizacion del dolar en una fecha dada."""

  TIPOS_VALIDOS = {
    "OFICIAL",
    "BLUE",
    "BOLSA",
    "CCL",
    "CRIPTO",
    "TARJETA",
    "MAYORISTA",
  }

  _next_id = 1

  def __init__(
    self,
    valor: float,
    fecha: date,
    tipo: str | TipoCotizacion,
    cotizacion_id: int | None = None,
    id: int | None = None,
  ) -> None:
    resolved_id = cotizacion_id if cotizacion_id is not None else id
    if resolved_id is None:
      resolved_id = CotizacionDolar._next_id
      CotizacionDolar._next_id += 1
    self.id = resolved_id
    self.valor = valor
    self.fecha = fecha
    self.tipo = tipo

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de cotizacion debe ser mayor a cero")
    self._id = value

  @property
  def valor(self) -> float:
    return self._valor

  @valor.setter
  def valor(self, value: float) -> None:
    if value <= 0:
      raise ValueError("La cotizacion debe ser positiva")
    self._valor = float(value)

  @property
  def fecha(self) -> date:
    return self._fecha

  @fecha.setter
  def fecha(self, value: date) -> None:
    self._fecha = value

  @property
  def tipo(self) -> str:
    return self._tipo

  @tipo.setter
  def tipo(self, value: str | TipoCotizacion) -> None:
    if isinstance(value, TipoCotizacion):
      raw = value.nombre
    else:
      raw = value
    normalizado = _normalize_tipo_nombre(raw)
    if normalizado not in self.TIPOS_VALIDOS:
      raise ValueError(f"Tipo de cotizacion invalido: {value}")
    self._tipo = normalizado


class Producto:
  """Entidad central del inventario."""

  def __init__(
    self,
    producto_id: int | None = None,
    nombre: str = "",
    descripcion: str = "",
    precio: Precio | None = None,
    categoria: Categoria | None = None,
    proveedor: Proveedor | None = None,
    id: int | None = None,
  ) -> None:
    resolved_id = producto_id if producto_id is not None else id
    if resolved_id is None:
      raise ValueError("Debe informar id de producto")
    self.id = resolved_id
    self.nombre = nombre
    self.descripcion = descripcion
    if precio is None or categoria is None or proveedor is None:
      raise ValueError("Producto requiere precio, categoria y proveedor")
    self.precio = precio
    self.categoria = categoria
    self.proveedor = proveedor

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de producto debe ser mayor a cero")
    self._id = value

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El nombre de producto no puede estar vacio")
    self._nombre = value.strip()

  @property
  def descripcion(self) -> str:
    return self._descripcion

  @descripcion.setter
  def descripcion(self, value: str) -> None:
    self._descripcion = value.strip()


class Stock:
  """Vincula un producto con un almacen y su cantidad."""

  def __init__(self, stock_id: int, producto: Producto, almacen: str, cantidad: int) -> None:
    self.id = stock_id
    self.producto = producto
    self.almacen = almacen
    self.cantidad = cantidad

  @property
  def id(self) -> int:
    return self._id

  @id.setter
  def id(self, value: int) -> None:
    if value <= 0:
      raise ValueError("El id de stock debe ser mayor a cero")
    self._id = value

  @property
  def almacen(self) -> str:
    return self._almacen

  @almacen.setter
  def almacen(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El almacen no puede estar vacio")
    self._almacen = value.strip()

  @property
  def cantidad(self) -> int:
    return self._cantidad

  @cantidad.setter
  def cantidad(self, value: int) -> None:
    if value < 0:
      raise ValueError("La cantidad no puede ser negativa")
    self._cantidad = int(value)
