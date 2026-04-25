from __future__ import annotations

from datetime import date
import json
import unicodedata
import urllib.error
import urllib.request
import re
from difflib import SequenceMatcher

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


def _fetch_dolar_rate(tipo: str) -> float:
  """Obtiene cotizacion desde API publica en tiempo real."""
  normalized = _normalizar_tipo(tipo)
  url = "https://dolarapi.com/v1/dolares"
  request = urllib.request.Request(
    url,
    headers={
      "User-Agent": "PriceManagerCLI/1.0 (+https://books.toscrape.com/)",
      "Accept": "application/json",
    },
  )
  try:
    with urllib.request.urlopen(request, timeout=10) as response:
      payload = json.loads(response.read().decode("utf-8"))
  except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
    payload = None

  by_tipo = {
    "OFICIAL": {"oficial"},
    "BLUE": {"blue"},
    "BOLSA": {"bolsa", "mep"},
    "CCL": {"contadoconliqui", "ccl"},
    "CRIPTO": {"cripto"},
    "TARJETA": {"tarjeta"},
    "MAYORISTA": {"mayorista"},
  }
  candidates = by_tipo.get(normalized, {normalized.lower()})
  if isinstance(payload, list):
    for row in payload:
      casa = str(row.get("casa", "")).lower().replace(" ", "")
      nombre = str(row.get("nombre", "")).lower().replace(" ", "")
      if any(candidate in casa or candidate in nombre for candidate in candidates):
        value = row.get("venta") or row.get("promedio")
        if value is None:
          continue
        return float(value)

  # Fallback por endpoint especifico por tipo (mas estable en algunos entornos).
  casa = next(iter(candidates))
  fallback_url = f"https://dolarapi.com/v1/dolares/{casa}"
  fallback_request = urllib.request.Request(
    fallback_url,
    headers={
      "User-Agent": "PriceManagerCLI/1.0 (+https://books.toscrape.com/)",
      "Accept": "application/json",
    },
  )
  try:
    with urllib.request.urlopen(fallback_request, timeout=10) as response:
      row = json.loads(response.read().decode("utf-8"))
      value = row.get("venta") or row.get("promedio")
      if value is None:
        raise RuntimeError("Respuesta sin campo de cotizacion")
      return float(value)
  except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
    raise RuntimeError("No se pudo consultar cotizacion online") from exc

  raise RuntimeError(f"No hay cotizacion online para tipo {normalized}")


class ServicioCompetenciaWeb:
  """Consulta precios de referencia en books.toscrape.com."""

  _BOOKS_BASE_URL = "https://books.toscrape.com/catalogue/"
  _BOOKS_INDEX = "https://books.toscrape.com/"

  @staticmethod
  def _fetch_page(url: str) -> str:
    try:
      with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError) as exc:
      raise RuntimeError("No se pudo consultar web de competencia") from exc

  def obtener_catalogo(self, limit: int = 40) -> list[dict[str, float | str]]:
    """Devuelve items [{title, price_gbp, url}] parseados desde books.toscrape."""
    url = self._BOOKS_INDEX
    items: list[dict[str, float | str]] = []
    while url and len(items) < limit:
      html = self._fetch_page(url)
      pattern = re.compile(
        r'<article class="product_pod".*?<h3><a href="(?P<href>[^"]+)" title="(?P<title>[^"]+)".*?'
        r'<p class="price_color">.?(?P<price>\d+\.\d+)</p>',
        re.S,
      )
      for match in pattern.finditer(html):
        href = match.group("href")
        title = match.group("title").strip()
        price = float(match.group("price"))
        full_url = self._BOOKS_BASE_URL + href.replace("../", "")
        items.append({"title": title, "price_gbp": price, "url": full_url})
        if len(items) >= limit:
          break
      next_match = re.search(r'<li class="next"><a href="([^"]+)"', html)
      if next_match:
        next_page = next_match.group(1)
        if "/catalogue/" in url:
          base = url.rsplit("/", 1)[0] + "/"
        else:
          base = self._BOOKS_BASE_URL
        url = base + next_page
      else:
        url = ""
    return items

  def comparar_producto(self, nombre_producto: str, precio_local: float) -> dict[str, float | str]:
    """Compara por similitud de nombre y devuelve mejor match encontrado."""
    catalog = self.obtener_catalogo(limit=60)
    if not catalog:
      raise RuntimeError("No se encontraron productos en la web de competencia")
    product_tokens = {tok for tok in re.split(r"\W+", nombre_producto.lower()) if tok}

    def score(item: dict[str, float | str]) -> tuple[float, int, float]:
      title = str(item["title"]).lower()
      title_tokens = {tok for tok in re.split(r"\W+", title) if tok}
      overlap = len(product_tokens & title_tokens)
      ratio = SequenceMatcher(None, nombre_producto.lower(), title).ratio()
      # desempata por menor diferencia de precio relativa
      competitor_price = float(item["price_gbp"])
      relative_diff = abs(precio_local - competitor_price)
      return (ratio, overlap, -relative_diff)

    ranking = sorted(catalog, key=score, reverse=True)
    best = ranking[0]
    best_ratio = score(best)[0]
    # Si el match es muy pobre, se informa ambiguedad con sugerencias.
    if best_ratio < 0.35:
      suggestions = ", ".join(str(item["title"]) for item in ranking[:5])
      raise RuntimeError(
        "Busqueda ambigua en competencia; sugerencias: "
        f"{suggestions}"
      )

    competitor_price = float(best["price_gbp"])
    diff = precio_local - competitor_price
    diff_pct = (diff / competitor_price * 100) if competitor_price else 0.0
    return {
      "competitor_title": str(best["title"]),
      "competitor_price_gbp": competitor_price,
      "competitor_url": str(best["url"]),
      "local_price": float(precio_local),
      "difference": diff,
      "difference_pct": diff_pct,
      "match_confidence": best_ratio * 100,
    }

class ServicioCategoria:
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


class ServicioMoneda:
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


class ServicioPrecio:
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


class ServicioTipoCotizacion:
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
  def __init__(
    self,
    repo: RepositorioCotizacionDolar,
    servicio_tipo_cotizacion: ServicioTipoCotizacion | None = None,
  ) -> None:
    self._repo = repo
    self._servicio_tipo_cotizacion = servicio_tipo_cotizacion

  def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self._repo.crear(cotizacion)

  def registrar_cotizacion(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self.crear(cotizacion)

  def buscar_por_id(self, cotizacion_id: int) -> CotizacionDolar | None:
    return self._repo.leer_por_id(cotizacion_id)

  def buscar_por_tipo_y_fecha(self, tipo: str, fecha_cotizacion: date) -> CotizacionDolar | None:
    return self._repo.leer_por_tipo_y_fecha(tipo, fecha_cotizacion)

  def listar_todos(self) -> list[CotizacionDolar]:
    return self._repo.leer_todos()

  def listar_historico_por_tipo(self, tipo: str) -> list[CotizacionDolar]:
    return self._repo.leer_historico_por_tipo(tipo)

  def obtener_historico(self, tipo_cotizacion_id: int) -> list[CotizacionDolar]:
    if self._servicio_tipo_cotizacion is None:
      raise ValueError("ServicioTipoCotizacion no configurado")
    tipo = self._servicio_tipo_cotizacion.buscar_por_id(tipo_cotizacion_id)
    if tipo is None:
      raise ValueError(f"No existe tipo de cotizacion con id {tipo_cotizacion_id}")
    return self._repo.leer_historico_por_tipo(_normalizar_tipo(tipo.nombre))

  def obtener_ultima_por_tipo(self, tipo: str) -> CotizacionDolar | None:
    historico = self._repo.leer_historico_por_tipo(_normalizar_tipo(tipo))
    if not historico:
      return None
    return historico[-1]

  def actualizar_cotizacion_tiempo_real(self, tipo: str = "OFICIAL") -> CotizacionDolar:
    valor = _fetch_dolar_rate(tipo)
    return self.crear(
      CotizacionDolar(
        valor=valor,
        fecha=date.today(),
        tipo=_normalizar_tipo(tipo),
      )
    )

  def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
    return self._repo.actualizar(cotizacion)

  def eliminar(self, cotizacion_id: int) -> bool:
    return self._repo.eliminar(cotizacion_id)


class ServicioProducto:
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
      return self._repo.crear(Stock(id=next_stock_id, producto=producto, almacen="GENERAL", cantidad=delta))

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
