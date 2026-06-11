from __future__ import annotations

import json
import sys
from pathlib import Path

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from price_manager.scraper.spiders.star_computacion_spider import StarComputacionSpider


def ejecutar_busqueda(
    query: str,
    max_results: int = 10,
    include_details: bool = True,
    debug_trace: bool = False,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    def _collect(item, response, spider):
        items.append(dict(item))

    dispatcher.connect(_collect, signal=signals.item_scraped)
    settings = get_project_settings()
    settings.setmodule("price_manager.scraper.settings", priority="project")

    process = CrawlerProcess(settings=settings)
    process.crawl(
        StarComputacionSpider,
        query=query,
        max_results=max_results,
        include_details=include_details,
        debug_trace=debug_trace,
    )
    process.start()
    dispatcher.disconnect(_collect, signal=signals.item_scraped)

    return items[:max_results]


def main() -> int:
    if len(sys.argv) < 2:
        print("[]")
        return 1

    query = sys.argv[1].strip()
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    include_details = True
    debug_trace = False
    if len(sys.argv) > 3:
        include_details = sys.argv[3].strip().lower() not in {"0", "false", "no"}
    if len(sys.argv) > 4:
        debug_trace = sys.argv[4].strip().lower() in {"1", "true", "yes", "si", "s"}
    resultados = ejecutar_busqueda(
        query=query,
        max_results=max_results,
        include_details=include_details,
        debug_trace=debug_trace,
    )
    print(json.dumps(resultados, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
