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

    def __init__(self, query: str, max_results: int = 10, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.query = query.strip()
        self.max_results = max(1, int(max_results))
        self._query_tokens = set(_normalize_text(self.query).split())
        self._seen_listing_urls: set[str] = set()
        self._seen_product_urls: set[str] = set()
        self._scheduled = 0

    def parse(self, response: scrapy.http.Response, **kwargs):
        self._seen_listing_urls.add(response.url)

        for product in response.css("a.product"):
            if self._scheduled >= self.max_results:
                break

            title = product.css("div.title *::text, div.title::text").getall()
            title_text = html.unescape(" ".join(part.strip() for part in title if part.strip()))
            href = product.attrib.get("href", "").strip()
            if not title_text or not href:
                continue

            match_score = self._match_score(title_text)
            if match_score <= 0:
                continue

            detail_url = response.urljoin(href)
            if detail_url in self._seen_product_urls:
                continue
            self._seen_product_urls.add(detail_url)
            self._scheduled += 1
            yield response.follow(
                detail_url,
                callback=self.parse_product,
                cb_kwargs={
                    "query": self.query,
                    "card_title": title_text,
                    "card_price": self._extract_card_price(product),
                    "match_score": match_score,
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
            yield response.follow(absolute, callback=self.parse)

    def parse_product(
        self,
        response: scrapy.http.Response,
        query: str,
        card_title: str,
        card_price: float | None,
        match_score: float,
    ):
        loader = StarProductLoader(item=StarProductItem(), response=response)
        loader.add_value("query", query)
        loader.add_value("url", response.url)
        loader.add_value("match_score", round(match_score, 4))

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

    def _match_score(self, title: str) -> float:
        title_tokens = set(_normalize_text(title).split())
        if not title_tokens or not self._query_tokens:
            return 0.0
        overlap = self._query_tokens & title_tokens
        if not overlap:
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
        return "/prods/" in parsed.path and "?" in url or parsed.path.endswith("/prods/") or parsed.path.count("/") > 2

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
