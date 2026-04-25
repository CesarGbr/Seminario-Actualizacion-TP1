from __future__ import annotations

from datetime import date
import unicodedata

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
from price_manager.repositories.repositories import (
  RepositorioCategoria,
  RepositorioCotizacionDolar,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioProducto,
  RepositorioProveedor,
  RepositorioStock,
  RepositorioTipoCotizacion,
)


def _normalizar_tipo(value: str) -> str:
  base = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
  normalizado = " ".join(base.strip().upper().split())
  if normalizado.startswith("DOLAR "):
    normalizado = normalizado.replace("DOLAR ", "", 1)
  return normalizado


class ServicioCategoria:
  """Capa de servicio para Categoria.

  Se inicializa con RepositorioCategoria y delega operaciones CRUD.
  """

  def __init__(self, repo: RepositorioCategoria) -> None:
    self._repo = repo

  def crear(self, categoria: Categoria) -> Categoria:
    return self._repo.crear(categoria)

  def buscar_por_id(self, categoria_id: int) -> Categoria | None:
    return self._repo.leer_por_id(categoria_id)

  def listar_todos(self) -> list[Categoria]:
    return self._repo.leer_todos()

  def actualizar(self, categoria: Categoria) -> Categoria:
    return self._repo.actualizar(categoria)

  def eliminar(self, categoria_id: int) -> bool:
    return self._repo.eliminar(categoria_id)


class ServicioProveedor:
  """Capa de servicio para Proveedor.

  Se inicializa con RepositorioProveedor y delega operaciones CRUD.
  """

  def __init__(self, repo: RepositorioProveedor) -> None:
    self._repo = repo

  def crear(self, proveedor: Proveedor) -> Proveedor:
    return self._repo.crear(proveedor)

  def buscar_por_id(self, proveedor_id: int) -> Proveedor | None:
    return self._repo.leer_por_id(proveedor_id)

  def listar_todos(self) -> list[Proveedor]:
    return self._repo.leer_todos()

  def actualizar(self, proveedor: Proveedor) -> Proveedor:
    return self._repo.actualizar(proveedor)

  def eliminar(self, proveedor_id: int) -> bool:
    return self._repo.eliminar(proveedor_id)


class ServicioPrecio:
  """Capa de servicio para Precio.

  Se inicializa con RepositorioPrecio y delega operaciones CRUD.
  """

  def __init__(self, repo: RepositorioPrecio) -> None:
    self._repo = repo

  def crear(self, precio: Precio) -> Precio:
    return self._repo.crear(precio)

  def buscar_por_id(self, precio_id: int) -> Precio | None:
    return self._repo.leer_por_id(precio_id)

  def listar_todos(self) -> list[Precio]:
    return self._repo.leer_todos()

  def actualizar(self, precio: Precio) -> Precio:
    return self._repo.actualizar(precio)

  def eliminar(self, precio_id: int) -> bool:
    return self._repo.eliminar(precio_id)


class ServicioMoneda:
  """Capa de servicio para Moneda."""

  def __init__(self, repo: RepositorioMoneda) -> None:
    self._repo = repo

  def crear(self, moneda: Moneda) -> Moneda:
    return self._repo.crear(moneda)

  def buscar_por_id(self, moneda_id: int) -> Moneda | None:
    return self._repo.leer_por_id(moneda_id)

  def listar_todos(self) -> list[Moneda]:
    return self._repo.leer_todos()

  def actualizar(self, moneda: Moneda) -> Moneda:
    return self._repo.actualizar(moneda)

  def eliminar(self, moneda_id: int) -> bool:
    return self._repo.eliminar(moneda_id)


class ServicioTipoCotizacion:
  """Capa de servicio para TipoCotizacion."""

  def __init__(self, repo: RepositorioTipoCotizacion) -> None:
    self._repo = repo

  def crear(self, tipo_cotizacion: TipoCotizacion) -> TipoCotizacion:
    return self._repo.crear(tipo_cotizacion)

  def buscar_por_id(self, tipo_cotizacion_id: int) -> TipoCotizacion | None:
    return self._repo.leer_por_id(tipo_cotizacion_id)

  def listar_todos(self) -> list[TipoCotizacion]:
    return self._repo.leer_todos()

  def actualizar(self, tipo_cotizacion: TipoCotizacion) -> TipoCotizacion:
    return self._repo.actualizar(tipo_cotizacion)

  def eliminar(self, tipo_cotizacion_id: int) -> bool:
    return self._repo.eliminar(tipo_cotizacion_id)


class ServicioCotizacionDolar:
  """Capa de servicio para CotizacionDolar.

  Se inicializa con RepositorioCotizacionDolar y expone busquedas
  especificas por tipo/fecha e historico por tipo.
  """

  def __init__(
    self,
    repo: RepositorioCotizacionDolar,
    servicio_tipo_cotizacion: ServicioTipoCotizacion | None = None,
  ) -> None:
    self._repo = repo
    self._servicio_tipo_cotizacion = servicio_tipo_cotizacion

  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self._repo.crear(cotizacion)

  def buscar_por_id(self, cotizacion_id: int) -> CotizacionDolar | None:
    return self._repo.leer_por_id(cotizacion_id)

  def buscar_por_tipo_y_fecha(self, tipo: str, fecha_cotizacion: date) -> CotizacionDolar | None:
    return self._repo.leer_por_tipo_y_fecha(tipo, fecha_cotizacion)

  def listar_todos(self) -> list[CotizacionDolar]:
    return self._repo.leer_todos()

  def listar_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
    return self._repo.leer_historico_por_tipo(tipo)

  def registrar_cotizacion(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self.crear(cotizacion)

  def obtener_historico(self, tipo_cotizacion_id: int) -> list[CotizacionDolar]:
    if self._servicio_tipo_cotizacion is None:
      raise ValueError("ServicioTipoCotizacion no configurado")
    tipo = self._servicio_tipo_cotizacion.buscar_por_id(tipo_cotizacion_id)
    if tipo is None:
      raise ValueError(f"No existe tipo de cotizacion con id {tipo_cotizacion_id}")
    return self._repo.leer_historico_por_tipo(_normalizar_tipo(tipo.nombre))

  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self._repo.actualizar(cotizacion)

  def eliminar(self, cotizacion_id: int) -> bool:
    return self._repo.eliminar(cotizacion_id)


class ServicioProducto:
  """Capa de servicio para Producto.

  Se inicializa con RepositorioProducto y con servicios auxiliares
  de Categoria y Proveedor para validar referencias antes de crear.
  """

  def __init__(
    self,
    repo: RepositorioProducto,
    servicio_categoria: ServicioCategoria,
    servicio_proveedor: ServicioProveedor,
  ) -> None:
    self._repo = repo
    self._servicio_categoria = servicio_categoria
    self._servicio_proveedor = servicio_proveedor

  def crear(self, producto: Producto) -> Producto:
    if self._servicio_categoria.buscar_por_id(producto.categoria.id) is None:
      raise ValueError(f"No existe categoria con id {producto.categoria.id}")
    if self._servicio_proveedor.buscar_por_id(producto.proveedor.id) is None:
      raise ValueError(f"No existe proveedor con id {producto.proveedor.id}")
    return self._repo.crear(producto)

  def buscar_por_id(self, producto_id: int) -> Producto | None:
    return self._repo.leer_por_id(producto_id)

  def obtener(self, producto_id: int) -> Producto:
    producto = self.buscar_por_id(producto_id)
    if producto is None:
      raise ValueError(f"No existe producto con id {producto_id}")
    return producto

  def listar_todos(self) -> list[Producto]:
    return self._repo.leer_todos()

  def actualizar(self, producto: Producto) -> Producto:
    return self._repo.actualizar(producto)

  def eliminar(self, producto_id: int) -> bool:
    eliminado = self._repo.eliminar(producto_id)
    if not eliminado:
      raise ValueError(f"No existe producto con id {producto_id}")
    return True


class ServicioStock:
  """Capa de servicio para Stock.

  Se inicializa con RepositorioStock y ServicioProducto para validar
  que el producto exista antes de registrar stock.
  """

  def __init__(self, repo: RepositorioStock, servicio_producto: ServicioProducto) -> None:
    self._repo = repo
    self._servicio_producto = servicio_producto

  def crear(self, stock: Stock) -> Stock:
    if self._servicio_producto.buscar_por_id(stock.producto.id) is None:
      raise ValueError(f"No existe producto con id {stock.producto.id}")
    return self._repo.crear(stock)

  def buscar_por_id(self, stock_id: int) -> Stock | None:
    return self._repo.leer_por_id(stock_id)

  def buscar_por_producto(self, producto_id: int) -> Stock | None:
    return self._repo.leer_por_producto(producto_id)

  def listar_todos(self) -> list[Stock]:
    return self._repo.leer_todos()

  def actualizar(self, stock: Stock) -> Stock:
    return self._repo.actualizar(stock)

  def eliminar_por_producto(self, producto_id: int) -> bool:
    return self._repo.eliminar(producto_id)

  def eliminar_por_id(self, stock_id: int) -> bool:
    return self._repo.eliminar_por_id(stock_id)

  def registrar_movimiento(self, producto_id: int, delta: int) -> Stock:
    stock = self.buscar_por_producto(producto_id)
    if stock is None:
      if delta < 0:
        raise ValueError("No se puede dejar stock en negativo")
      producto = self._servicio_producto.buscar_por_id(producto_id)
      if producto is None:
        raise ValueError(f"No existe producto con id {producto_id}")
      next_stock_id = len(self._repo.leer_todos()) + 1
      return self._repo.crear(Stock(next_stock_id, producto, "GENERAL", delta))

    nueva_cantidad = stock.cantidad + delta
    if nueva_cantidad < 0:
      raise ValueError("No se puede dejar stock en negativo")
    stock.cantidad = nueva_cantidad
    return self._repo.actualizar(stock)

  def obtener_stock(self, producto_id: int) -> int:
    stock = self.buscar_por_producto(producto_id)
    if stock is None:
      raise ValueError(f"No existe stock para producto {producto_id}")
    return stock.cantidad
