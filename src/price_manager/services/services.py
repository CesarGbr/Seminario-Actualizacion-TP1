# %%writefile price_manager/services/services.py

from __future__ import annotations

from datetime import date
import html
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

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


class ConfiguracionRequeridaError(RuntimeError):
    """Error de configuracion para integraciones opcionales."""


_DOTENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)


def _get_api_url() -> str:
    configured = (os.getenv("API_URL") or "").strip()
    if not configured:
        raise ConfiguracionRequeridaError(
            "Falta API_URL en .env para usar cotizaciones online."
        )
    return configured


def _parse_float(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip().replace(",", ".")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_json_url(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PriceManagerCLI/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_dolares_payload() -> list[dict[str, Any]]:
    try:
        payload = _read_json_url(_get_api_url())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("No se pudo consultar cotizacion online") from exc

    if not isinstance(payload, list):
        raise RuntimeError("Respuesta invalida de API de cotizaciones")

    resultado = [item for item in payload if isinstance(item, dict)]
    if not resultado:
        raise RuntimeError("La API no devolvio cotizaciones")

    return resultado


def _fecha_desde_payload(row: dict[str, Any]) -> date:
    raw = str(row.get("fechaActualizacion") or row.get("fecha") or "").strip()
    if not raw:
        return date.today()

    candidate = raw.replace("Z", "+00:00")
    if "T" in candidate:
        candidate = candidate.split("T", 1)[0]
    else:
        candidate = candidate[:10]

    try:
        return date.fromisoformat(candidate)
    except ValueError:
        return date.today()


def _normalizar_tipo(value: str) -> str:
    base = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
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
    try:
        payload = _fetch_dolares_payload()
    except RuntimeError:
        payload = []

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
    for row in payload:
        casa = str(row.get("casa", "")).lower().replace(" ", "")
        nombre = str(row.get("nombre", "")).lower().replace(" ", "")
        if any(candidate in casa or candidate in nombre for candidate in candidates):
            value = _parse_float(row.get("venta") or row.get("promedio"))
            if value is None:
                continue
            return value

    # Fallback por endpoint especifico por tipo (mas estable en algunos entornos).
    casa = next(iter(candidates))
    fallback_url = f"{_get_api_url().rstrip('/')}/{casa}"
    try:
        row = _read_json_url(fallback_url)
        if not isinstance(row, dict):
            raise RuntimeError("Respuesta sin estructura valida")
        value = _parse_float(row.get("venta") or row.get("promedio"))
        if value is None:
            raise RuntimeError("Respuesta sin campo de cotizacion")
        return value
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("No se pudo consultar cotizacion online") from exc

    raise RuntimeError(f"No hay cotizacion online para tipo {normalized}")


class ServicioCompetenciaWeb:
    """Consulta precios de referencia en Star Computacion."""

    _STAR_BASE_URL = "https://www.starcomputacion.com.ar/"
    _STAR_PRODUCTS_URL = urllib.parse.urljoin(_STAR_BASE_URL, "prods/")
    _STAR_PRODUCTS_FALLBACK = _STAR_BASE_URL
    _STOPWORDS_MATCH = {
        "de",
        "del",
        "la",
        "el",
        "los",
        "las",
        "y",
        "con",
        "para",
        "por",
        "en",
        "a",
        "un",
        "una",
        "tipo",
    }

    @classmethod
    def _fetch_page(cls, url: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, 4):
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        ),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
                        "Referer": cls._STAR_BASE_URL,
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                    },
                )
                with urllib.request.urlopen(request, timeout=20) as response:
                    return response.read().decode("utf-8", errors="ignore")
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                if attempt < 3:
                    time.sleep(0.8 * attempt)
        raise RuntimeError("No se pudo consultar web de competencia") from last_exc

    @staticmethod
    def _parse_price_ars(raw_price: str) -> float | None:
        match = re.search(r"ARS\s*([\d\.\,]+)", raw_price, re.I)
        if not match:
            return None
        numeric = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(numeric)
        except ValueError:
            return None

    @classmethod
    def _tokenize_for_match(cls, text: str) -> list[str]:
        tokens = [t for t in re.split(r"\W+", text.lower()) if t]
        return [t for t in tokens if t not in cls._STOPWORDS_MATCH]

    @classmethod
    def _extract_anchor_tokens(cls, text: str) -> set[str]:
        anchors = set()
        for token in cls._tokenize_for_match(text):
            if len(token) >= 4 and not token.isdigit():
                anchors.add(token)
        return anchors

    def obtener_catalogo(self, limit: int = 40) -> list[dict[str, float | str]]:
        """Devuelve items [{title, price_ars, url}] parseados desde Star."""
        items: list[dict[str, float | str]] = []
        product_pattern = re.compile(
            r'<a\s+class="product"\s+href="(?P<href>[^"]+)".*?</a>',
            re.S | re.I,
        )
        for source_url in (self._STAR_PRODUCTS_URL, self._STAR_PRODUCTS_FALLBACK):
            page_html = self._fetch_page(source_url)
            for product_match in product_pattern.finditer(page_html):
                block = product_match.group(0)
                href = product_match.group("href").strip()

                title_match = re.search(
                    r'<div\s+class="title">\s*(?P<title>.*?)\s*</div>',
                    block,
                    re.S | re.I,
                )
                if title_match:
                    title = html.unescape(title_match.group("title")).strip()
                else:
                    alt_match = re.search(r'alt="(?P<alt>[^"]+)"', block, re.I)
                    title = (
                        html.unescape(alt_match.group("alt")).strip()
                        if alt_match
                        else ""
                    )
                if not title:
                    continue

                price_match = re.search(
                    r'<div\s+class="price">\s*(?P<price_text>.*?)\s*</div>',
                    block,
                    re.S | re.I,
                )
                if not price_match:
                    continue
                price_ars = self._parse_price_ars(price_match.group("price_text"))
                if price_ars is None:
                    continue

                full_url = urllib.parse.urljoin(self._STAR_BASE_URL, href)
                items.append({"title": title, "price_ars": price_ars, "url": full_url})
                if len(items) >= limit:
                    return items
            if items:
                return items
        return items

    def comparar_producto(
        self, nombre_producto: str, precio_local: float
    ) -> dict[str, float | str]:
        """Compara por similitud de nombre y devuelve mejor match encontrado."""
        ranking = self._rank_catalog(nombre_producto, precio_local, limit=120)
        if not ranking:
            raise RuntimeError("No se encontraron productos en la web de competencia")
        best, best_ratio = ranking[0]
        # Si el match es muy pobre, se informa ambiguedad con sugerencias.
        if best_ratio < 0.52:
            suggestions = ", ".join(str(item["title"]) for item, _ in ranking[:5])
            raise RuntimeError(
                "Busqueda ambigua en competencia; sugerencias: " f"{suggestions}"
            )
        return self._build_result(best, precio_local, best_ratio)

    def sugerir_productos(
        self, nombre_producto: str, precio_local: float, limit: int = 5
    ) -> list[dict[str, float | str]]:
        ranking = self._rank_catalog(nombre_producto, precio_local, limit=120)
        suggestions: list[dict[str, float | str]] = []
        for item, ratio in ranking[: max(1, limit)]:
            suggestions.append(
                {
                    "title": str(item["title"]),
                    "price_ars": float(item["price_ars"]),
                    "url": str(item["url"]),
                    "match_confidence": ratio * 100,
                }
            )
        return suggestions

    def comparar_producto_con_titulo(
        self, nombre_producto: str, precio_local: float, competitor_title: str
    ) -> dict[str, float | str]:
        catalog = self.obtener_catalogo(limit=120)
        if not catalog:
            raise RuntimeError("No se encontraron productos en la web de competencia")
        expected = competitor_title.strip().lower()
        for item in catalog:
            if str(item["title"]).strip().lower() == expected:
                ratio = SequenceMatcher(
                    None, nombre_producto.lower(), str(item["title"]).lower()
                ).ratio()
                return self._build_result(item, precio_local, ratio)
        raise RuntimeError("La sugerencia elegida ya no se encuentra disponible")

    def _rank_catalog(
        self, nombre_producto: str, precio_local: float, limit: int = 120
    ) -> list[tuple[dict[str, float | str], float]]:
        catalog = self.obtener_catalogo(limit=limit)
        if not catalog:
            return []
        product_tokens = set(self._tokenize_for_match(nombre_producto))
        anchor_tokens = self._extract_anchor_tokens(nombre_producto)

        filtered_catalog = catalog
        if anchor_tokens:
            with_overlap = []
            for item in catalog:
                title_tokens = set(self._tokenize_for_match(str(item["title"])))
                if anchor_tokens & title_tokens:
                    with_overlap.append(item)
            if with_overlap:
                filtered_catalog = with_overlap

        def score(item: dict[str, float | str]) -> tuple[float, int, float]:
            title = str(item["title"]).lower()
            title_tokens = set(self._tokenize_for_match(title))
            overlap = len(product_tokens & title_tokens)
            base_ratio = SequenceMatcher(None, nombre_producto.lower(), title).ratio()
            token_ratio = (
                overlap / max(1, len(product_tokens)) if product_tokens else 0.0
            )
            ratio = (base_ratio * 0.6) + (token_ratio * 0.4)
            competitor_price = float(item["price_ars"])
            relative_diff = abs(precio_local - competitor_price)
            return (ratio, overlap, -relative_diff)

        ranking = sorted(filtered_catalog, key=score, reverse=True)
        return [(item, score(item)[0]) for item in ranking]

    @staticmethod
    def _build_result(
        competitor_item: dict[str, float | str],
        precio_local: float,
        match_ratio: float,
    ) -> dict[str, float | str]:
        competitor_price = float(competitor_item["price_ars"])
        diff = precio_local - competitor_price
        diff_pct = (diff / competitor_price * 100) if competitor_price else 0.0
        return {
            "competitor_title": str(competitor_item["title"]),
            "competitor_price_ars": competitor_price,
            "competitor_url": str(competitor_item["url"]),
            "local_price": float(precio_local),
            "difference": diff,
            "difference_pct": diff_pct,
            "match_confidence": match_ratio * 100,
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

    def buscar_por_tipo_y_fecha(
        self, tipo: str, fecha_cotizacion: date
    ) -> CotizacionDolar | None:
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
            raise ValueError(
                f"No existe tipo de cotizacion con id {tipo_cotizacion_id}"
            )
        return self._repo.leer_historico_por_tipo(_normalizar_tipo(tipo.nombre))

    def obtener_ultima_por_tipo(self, tipo: str) -> CotizacionDolar | None:
        historico = self._repo.leer_historico_por_tipo(_normalizar_tipo(tipo))
        if not historico:
            return None
        return historico[-1]

    def _siguiente_id_cotizacion(self) -> int:
        return max((item.id for item in self._repo.leer_todos()), default=0) + 1

    def obtener_cotizaciones(self) -> list[CotizacionDolar]:
        """Descarga cotizaciones desde API_URL y las registra en base de datos."""
        payload = _fetch_dolares_payload()
        registradas: list[CotizacionDolar] = []
        siguiente_id = self._siguiente_id_cotizacion()

        for row in payload:
            tipo_raw = str(row.get("nombre") or row.get("casa") or "").strip()
            if not tipo_raw:
                continue

            tipo = _normalizar_tipo(tipo_raw)
            if tipo not in CotizacionDolar.TIPOS_VALIDOS:
                continue

            valor = _parse_float(row.get("venta") or row.get("promedio"))
            if valor is None or valor <= 0:
                continue

            fecha_cotizacion = _fecha_desde_payload(row)
            existente = self.buscar_por_tipo_y_fecha(tipo, fecha_cotizacion)

            if existente is None:
                cotizacion = self.crear(
                    CotizacionDolar(
                        id=siguiente_id,
                        valor=valor,
                        fecha=fecha_cotizacion,
                        tipo=tipo,
                    )
                )
                siguiente_id += 1
            else:
                existente.valor = valor
                cotizacion = self.actualizar(existente)

            registradas.append(cotizacion)

        if not registradas:
            raise RuntimeError("No se obtuvieron cotizaciones validas desde la API")

        return registradas

    def actualizar_cotizacion_tiempo_real(
        self, tipo: str = "OFICIAL"
    ) -> CotizacionDolar:
        valor = _fetch_dolar_rate(tipo)
        tipo_normalizado = _normalizar_tipo(tipo)
        fecha_hoy = date.today()
        existente = self.buscar_por_tipo_y_fecha(tipo_normalizado, fecha_hoy)

        if existente is None:
            return self.crear(
                CotizacionDolar(
                    id=self._siguiente_id_cotizacion(),
                    valor=valor,
                    fecha=fecha_hoy,
                    tipo=tipo_normalizado,
                )
            )

        existente.valor = valor
        return self.actualizar(existente)

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
    def __init__(
        self, repo: RepositorioStock, servicio_producto: ServicioProducto
    ) -> None:
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
            return self._repo.crear(
                Stock(
                    id=next_stock_id,
                    producto=producto,
                    almacen="GENERAL",
                    cantidad=delta,
                )
            )

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
