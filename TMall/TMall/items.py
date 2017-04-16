# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TmallItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    simpleIntroduction = scrapy.Field()   # 名称
    price = scrapy.Field()   # 价格
    url = scrapy.Field()    # 网站链接

