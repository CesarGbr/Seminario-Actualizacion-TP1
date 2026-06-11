from __future__ import annotations

import scrapy


class StarProductItem(scrapy.Item):
    query = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    price_ars = scrapy.Field()
    payment_options = scrapy.Field()
    description = scrapy.Field()
    match_score = scrapy.Field()
    source_order = scrapy.Field()
