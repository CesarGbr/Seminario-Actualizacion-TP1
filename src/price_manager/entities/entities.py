from __future__ import annotations

from datetime import date


class Categoria:
  """Representa el rubro de un producto."""

  def __init__(self, categoria_id: int, nombre: str) -> None:
    self.id = categoria_id
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

  def __init__(self, proveedor_id: int, nombre_legal: str, contacto: str) -> None:
    self.id = proveedor_id
    self.nombre_legal = nombre_legal
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


class Precio:
  """Representa el valor monetario de un producto."""

  def __init__(
    self,
    precio_id: int,
    valor: float,
    moneda: str,
    fecha_actualizacion: date | None = None,
  ) -> None:
    self.id = precio_id
    self.valor = valor
    self.moneda = moneda
    self.fecha_actualizacion = fecha_actualizacion or date.today()

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
  def moneda(self, value: str) -> None:
    codigo = value.strip().upper()
    if len(codigo) != 3 or not codigo.isalpha():
      raise ValueError("La moneda debe ser un codigo de 3 letras")
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

  def __init__(self, cotizacion_id: int, valor: float, fecha: date, tipo: str) -> None:
    self.id = cotizacion_id
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
  def tipo(self, value: str) -> None:
    normalizado = value.strip().upper()
    if normalizado not in self.TIPOS_VALIDOS:
      raise ValueError(f"Tipo de cotizacion invalido: {value}")
    self._tipo = normalizado


class Producto:
  """Entidad central del inventario."""

  def __init__(
    self,
    producto_id: int,
    nombre: str,
    descripcion: str,
    precio: Precio,
    categoria: Categoria,
    proveedor: Proveedor,
  ) -> None:
    self.id = producto_id
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
