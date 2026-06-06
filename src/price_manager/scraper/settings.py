BOT_NAME = "price_manager_star"

SPIDER_MODULES = ["price_manager.scraper.spiders"]
NEWSPIDER_MODULE = "price_manager.scraper.spiders"

ROBOTSTXT_OBEY = False
LOG_ENABLED = False
COOKIES_ENABLED = False
DOWNLOAD_TIMEOUT = 20
RETRY_TIMES = 2

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}

ITEM_PIPELINES = {
    "price_manager.scraper.pipelines.StarProductPipeline": 300,
}
