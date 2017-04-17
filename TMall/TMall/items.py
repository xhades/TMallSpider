# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TmallItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    prodId = scrapy.Field()
    type = scrapy.Field()
    start_time = scrapy.Field()
    youhui = scrapy.Field()
    huodong = scrapy.Field()
    yuanjia = scrapy.Field()
    xianjia = scrapy.Field()
    end_time = scrapy.Field()
    title = scrapy.Field()
