from __future__ import annotations

import html
import json
import re
import unicodedata
import urllib.parse

import scrapy

from price_manager.scraper.items import StarProductItem
from price_manager.scraper.loaders import StarProductLoader


def _normalize_text(value: str) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return " ".join(ascii_text.lower().split())


class StarComputacionSpider(scrapy.Spider):
    name = "star_computacion"
    allowed_domains = ["starcomputacion.com.ar"]
    start_urls = ["https://www.starcomputacion.com.ar/prods/"]
    _ALLOWED_LISTING_QUERY_KEYS = {"page", "pagina", "p", "order", "sort"}
    _GENERIC_PRODUCT_TOKENS = {
        "adaptador",
        "auricular",
        "auriculares",
        "cable",
        "camara",
        "desktop",
        "disco",
        "fuente",
        "gabinete",
        "impresora",
        "memoria",
        "microfono",
        "monitor",
        "mouse",
        "notebook",
        "placa",
        "router",
        "ssd",
        "teclado",
        "webcam",
    }

    def __init__(
        self,
        query: str,
        max_results: int = 10,
        include_details: bool = True,
        debug_trace: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.query = query.strip()
        self.max_results = max(1, int(max_results))
        self.include_details = str(include_details).lower() not in {"0", "false", "no"}
        self.debug_trace = str(debug_trace).lower() in {"1", "true", "yes", "si", "s"}
        self._query_tokens = set(_normalize_text(self.query).split())
        self._specific_query_tokens = {
            token
            for token in self._query_tokens
            if token not in self._GENERIC_PRODUCT_TOKENS
        }
        self._seen_listing_urls: set[str] = set()
        self._seen_product_urls: set[str] = set()
        self._scheduled = 0
        self._listing_pages_visited = 0

    def parse(self, response: scrapy.http.Response, **kwargs):
        self._seen_listing_urls.add(response.url)
        self._listing_pages_visited += 1
        self._debug(
            f"parse url={response.url} status={response.status} "
            f"query='{self.query}' tokens={sorted(self._query_tokens)} "
            f"specific_tokens={sorted(self._specific_query_tokens)} "
            f"listing_pages_visited={self._listing_pages_visited}"
        )

        for index, product in enumerate(response.css("a.product"), start=1):
            if self._scheduled >= self.max_results:
                self._debug(f"limite alcanzado: scheduled={self._scheduled}")
                break

            title = product.css("div.title *::text, div.title::text").getall()
            title_text = html.unescape(" ".join(part.strip() for part in title if part.strip()))
            href = product.attrib.get("href", "").strip()
            if not title_text or not href:
                self._debug(f"descartado card sin titulo/href index={index}")
                continue

            match_score = self._match_score(title_text)
            if match_score <= 0:
                self._debug(
                    f"descartado por match index={index} title='{title_text}' "
                    f"score={match_score:.4f}"
                )
                continue

            detail_url = response.urljoin(href)
            if detail_url in self._seen_product_urls:
                self._debug(f"descartado duplicado url={detail_url}")
                continue
            self._seen_product_urls.add(detail_url)
            self._scheduled += 1
            self._debug(
                f"aceptado index={index} title='{title_text}' "
                f"score={match_score:.4f} detail_url={detail_url}"
            )
            if not self.include_details:
                yield self._build_listing_item(
                    title=title_text,
                    url=detail_url,
                    card_price=self._extract_card_price(product),
                    match_score=match_score,
                    source_order=index,
                )
                continue
            yield response.follow(
                detail_url,
                callback=self.parse_product,
                cb_kwargs={
                    "query": self.query,
                    "card_title": title_text,
                    "card_price": self._extract_card_price(product),
                    "match_score": match_score,
                    "source_order": index,
                },
            )

        if self._scheduled >= self.max_results:
            return

        for href in response.css("a::attr(href)").getall():
            absolute = response.urljoin(href)
            if not self._is_listing_url(absolute):
                continue
            if absolute in self._seen_listing_urls:
                continue
            self._seen_listing_urls.add(absolute)
            self._debug(f"siguiendo listado url={absolute}")
            yield response.follow(absolute, callback=self.parse)

    def parse_product(
        self,
        response: scrapy.http.Response,
        query: str,
        card_title: str,
        card_price: float | None,
        match_score: float,
        source_order: int,
    ):
        self._debug(
            f"parse_product url={response.url} status={response.status} "
            f"card_title='{card_title}' score={match_score:.4f}"
        )
        loader = StarProductLoader(item=StarProductItem(), response=response)
        loader.add_value("query", query)
        loader.add_value("url", response.url)
        loader.add_value("match_score", match_score)
        loader.add_value("source_order", source_order)

        title = (
            response.css("h1::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or card_title
        )
        loader.add_value("title", html.unescape(title or card_title))

        image_url = (
            response.css("meta[property='og:image']::attr(content)").get()
            or response.css("img::attr(src)").get()
            or ""
        )
        if image_url:
            loader.add_value("image_url", response.urljoin(image_url))

        price_text = " ".join(
            response.css(".price::text, .price *::text, [class*='price']::text").getall()
        )
        if price_text:
            loader.add_value("price_ars", price_text)
        elif card_price is not None:
            loader.add_value("price_ars", str(card_price))

        payments = self._extract_payment_options(response)
        if payments:
            loader.add_value("payment_options", payments)

        description = self._extract_description(response)
        if description:
            loader.add_value("description", description)

        yield loader.load_item()

    def _build_listing_item(
        self,
        title: str,
        url: str,
        card_price: float | None,
        match_score: float,
        source_order: int,
    ) -> StarProductItem:
        loader = StarProductLoader(item=StarProductItem())
        loader.add_value("query", self.query)
        loader.add_value("title", title)
        loader.add_value("url", url)
        if card_price is not None:
            loader.add_value("price_ars", str(card_price))
        loader.add_value("match_score", match_score)
        loader.add_value("source_order", source_order)
        loader.add_value("image_url", "")
        loader.add_value("payment_options", "")
        loader.add_value("description", "")
        return loader.load_item()

    def _debug(self, message: str) -> None:
        if self.debug_trace:
            self.logger.info("[TRACE] %s", message)

    def _match_score(self, title: str) -> float:
        title_tokens = set(_normalize_text(title).split())
        if not title_tokens:
            return 0.0
        if not self._query_tokens:
            return 1.0
        overlap = self._query_tokens & title_tokens
        if not overlap:
            return 0.0
        specific_overlap = self._specific_query_tokens & title_tokens
        if self._specific_query_tokens and not specific_overlap:
            return 0.0
        if len(self._query_tokens) >= 3 and len(overlap) < 2 and not specific_overlap:
            return 0.0
        return len(overlap) / len(self._query_tokens)

    @staticmethod
    def _extract_card_price(product: scrapy.selector.Selector) -> float | None:
        price_text = " ".join(
            product.css("div.price::text, div.price *::text").getall()
        )
        match = re.search(r"ARS\s*([\d\.\,]+)", price_text, re.I)
        if not match:
            return None
        try:
            return float(match.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _is_listing_url(url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc and "starcomputacion.com.ar" not in parsed.netloc:
            return False
        if not parsed.path.endswith("/prods/"):
            return False
        if not parsed.query:
            return True

        query_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        query_keys = {key.strip().lower() for key in query_params if key.strip()}
        if not query_keys:
            return True
        return query_keys.issubset(StarComputacionSpider._ALLOWED_LISTING_QUERY_KEYS)

    @staticmethod
    def _extract_payment_options(response: scrapy.http.Response) -> list[str]:
        candidates = response.css(
            ".payments *::text, .payment *::text, .cuotas *::text, [class*='cuota']::text"
        ).getall()
        normalized = [" ".join(text.split()) for text in candidates if text.strip()]
        filtered = [
            text
            for text in normalized
            if any(token in text.lower() for token in ("cuota", "tarjeta", "transfer", "efectivo"))
        ]
        if filtered:
            return filtered[:10]

        regex_matches = re.findall(
            r"((?:\d+\s*x\s*)?ARS\s*[\d\.\,]+[^<\n]{0,80})",
            response.text,
            re.I,
        )
        return [" ".join(match.split()) for match in regex_matches[:10]]

    @staticmethod
    def _extract_description(response: scrapy.http.Response) -> str:
        selectors = [
            ".description *::text",
            ".product-description *::text",
            ".descripcion *::text",
            "[class*='description'] *::text",
        ]
        for selector in selectors:
            values = [text.strip() for text in response.css(selector).getall() if text.strip()]
            if values:
                return " ".join(values)

        for script_text in response.css("script[type='application/ld+json']::text").getall():
            try:
                payload = json.loads(script_text)
            except json.JSONDecodeError:
                continue
            description = payload.get("description") if isinstance(payload, dict) else None
            if description:
                return str(description)

        meta_description = response.css("meta[name='description']::attr(content)").get()
        return meta_description or ""
