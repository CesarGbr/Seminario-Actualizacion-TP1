from __future__ import annotations

from datetime import date
import unicodedata


def _normalize_tipo_nombre(value: str) -> str:
  base = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
  normalizado = " ".join(base.strip().upper().split())
  if normalizado.startswith("DOLAR "):
    normalizado = normalizado.replace("DOLAR ", "", 1)
  if "BLUE" in normalizado:
    return "BLUE"
  if "OFICIAL" in normalizado:
    return "OFICIAL"
  if "BOLSA" in normalizado:
    return "BOLSA"
  if "CCL" in normalizado:
    return "CCL"
  if "CRIPTO" in normalizado:
    return "CRIPTO"
  if "TARJETA" in normalizado:
    return "TARJETA"
  if "MAYORISTA" in normalizado:
    return "MAYORISTA"
  return normalizado


class Categoria:
  def __init__(self, id: int, nombre: str) -> None:
    self.id = id
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
  def __init__(self, id: int, nombre: str, contacto: str) -> None:
    self.id = id
    self.nombre = nombre
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
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El nombre de proveedor no puede estar vacio")
    self._nombre = value.strip()

  @property
  def nombre_legal(self) -> str:
    return self._nombre

  @nombre_legal.setter
  def nombre_legal(self, value: str) -> None:
    self.nombre = value

  @property
  def contacto(self) -> str:
    return self._contacto

  @contacto.setter
  def contacto(self, value: str) -> None:
    if not value.strip():
      raise ValueError("El contacto no puede estar vacio")
    self._contacto = value.strip()


class Moneda:
  def __init__(self, id: int, nombre: str) -> None:
    self.id = id
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
  def __init__(self, id: int, nombre: str) -> None:
    self.id = id
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
  _next_id = 1

  def __init__(
    self,
    valor: float,
    moneda: str | Moneda,
    fecha: date | None = None,
    id: int | None = None,
  ) -> None:
    self.id = id if id is not None else self._next_id
    if id is None:
      Precio._next_id += 1
    self.valor = valor
    self.moneda = moneda
    self.fecha_actualizacion = fecha or date.today()

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

  def __init__(self, valor: float, fecha: date, tipo: str | TipoCotizacion, id: int | None = None) -> None:
    self.id = id if id is not None else self._next_id
    if id is None:
      CotizacionDolar._next_id += 1
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
    raw = value.nombre if isinstance(value, TipoCotizacion) else value
    normalizado = _normalize_tipo_nombre(raw)
    if normalizado not in self.TIPOS_VALIDOS:
      raise ValueError(f"Tipo de cotizacion invalido: {value}")
    self._tipo = normalizado


class Producto:
  def __init__(
    self,
    id: int,
    nombre: str,
    descripcion: str,
    precio: Precio,
    categoria: Categoria,
    proveedor: Proveedor,
  ) -> None:
    self.id = id
    self.nombre = nombre
    self.descripcion = descripcion
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
  def __init__(self, id: int, producto: Producto, almacen: str, cantidad: int) -> None:
    self.id = id
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
