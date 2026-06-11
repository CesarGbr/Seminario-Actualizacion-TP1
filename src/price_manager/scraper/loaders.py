from __future__ import annotations

import re

from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _clean_description(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned


def _clean_price(value: str) -> float | None:
    match = re.search(r"([\d\.\,]+)", value)
    if not match:
        return None
    normalized = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _clean_score(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _clean_order(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class StarProductLoader(ItemLoader):
    default_output_processor = TakeFirst()

    query_in = MapCompose(str.strip, _clean_text)
    query_out = TakeFirst()

    title_in = MapCompose(str.strip, _clean_text)
    title_out = TakeFirst()

    url_in = MapCompose(str.strip)
    url_out = TakeFirst()

    image_url_in = MapCompose(str.strip)
    image_url_out = TakeFirst()

    price_ars_in = MapCompose(str.strip, _clean_price)
    price_ars_out = TakeFirst()

    description_in = MapCompose(_clean_description)
    description_out = TakeFirst()

    payment_options_in = MapCompose(_clean_text)
    payment_options_out = Join(" | ")

    match_score_in = MapCompose(_clean_score)
    match_score_out = TakeFirst()

    source_order_in = MapCompose(_clean_order)
    source_order_out = TakeFirst()
