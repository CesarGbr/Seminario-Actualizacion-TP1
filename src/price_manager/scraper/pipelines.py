from __future__ import annotations

from collections import defaultdict

from scrapy.exceptions import DropItem


class StarProductPipeline:
    """Normaliza y limita resultados por consulta."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = defaultdict(int)

    def process_item(self, item, spider):
        query = str(item.get("query") or "").strip()
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        price = item.get("price_ars")

        if not query:
            raise DropItem("Resultado sin query asociada")
        if not title or not url:
            raise DropItem("Resultado incompleto")
        if price is None:
            raise DropItem("Resultado sin precio")

        self._counts[query] += 1
        if self._counts[query] > getattr(spider, "max_results", 10):
            raise DropItem("Se supero el limite por busqueda")

        description = str(item.get("description") or "").strip()
        item["description"] = description or "Descripcion no disponible."

        payment_options = item.get("payment_options")
        if not payment_options:
            item["payment_options"] = "Formas de pago no disponibles."

        image_url = str(item.get("image_url") or "").strip()
        if not image_url:
            item["image_url"] = ""

        return item
