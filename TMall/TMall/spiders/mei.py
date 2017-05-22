# !/usr/bin/env python
# encoding=utf-8

"""
@author: xhades
@Date: 2017/5/22

"""
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import scrapy
from scrapy.spiders import CrawlSpider
import logging
import json
import time
from scrapy.selector import Selector
import re
from scrapy.selector import Selector
from TMall.items import TmallItem, TmallReviewsItem
from time import sleep


class TmallSpider(CrawlSpider):
    name = 'tm'
    custom_settings = {'ITEM_PIPELINES': {'TMall.pipelines.TmallPipeline': 300}}

    def __init__(self):
        super(TmallSpider, self).__init__()
        self.allowed_domains = ['https://www.tmall.com/']
        self.start_urls = ['https://lovo.tmall.com/view_shop.htm?spm=a1z10.1-b-s.w5001-14406249609.11.rV6UL8&type=p&from=inshophq_1_0&newHeader_b=s_from&searcy_type=item&keyword=%CB%C4%BC%FE%CC%D7&search=y&orderType=defaultSort&tsearch=y&scene=taobao_shop']
        self.itemid='21479223750'

        # items xpath
        self.simpleIntroduction_xpath = "//div[@class='tb-detail-hd']/h1"
        self.price_xpath = "//span[@class='tm-price']"

        # parse page settings
        self.start_page = 1
        self.end_page = 1

    @staticmethod
    def get_name():
        pass

    def parse(self, response):
        logging.info("=====GET SUCCESS=======")
        for page in xrange(self.start_page, self.end_page+1):     # NOTE: 此处url会发生变化
            url = 'https://luolai.tmall.com/i/asynSearch.htm?_ksTS=1495458822836_127&callback=jsonp128&mid=' \
                  'w-14406186979-0&wid=14406186979&path=/search.htm&&search=y&pageNo={}&tsearch=y'.format(page)
            yield scrapy.Request(url, callback=self.parse_page, dont_filter=True)

    def parse_page(self, response):
        logging.info("=====PARSE NEXT PAGE=======")

        href_list = response.xpath("//a[contains(@class, 'J_TGoldData')]").extract()

        id_list = [re.search("id=(\d+)&", href).group(1) for href in href_list]
        print id_list
        for id in id_list:
            url = "https://detail.m.tmall.com/item.htm?id={}".format(id)
            yield scrapy.Request(url, dont_filter=True, callback=self.parse_item, meta={'id':id})

    def parse_item(self, response):

        logging.info("=====START PARSER ITEM=======")
        data_detail = re.findall('_DATA_Detail = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_mdskip = re.findall('_DATA_Mdskip = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_detail_js = json.loads(data_detail[0])
        data_mdskip_js = json.loads(data_mdskip[0])

        try:
            spuid = re.search('spuId.*\"(\d+)?\"', data_detail[0]).group(1)
            sellerid = re.search("sellerId=(\d+)", data_detail[0]).group(1)
        except:
            spuid = ''
            sellerid = ''
        html = response.body.decode('gbk', 'ignore')

        title = response.xpath('//section[@id="s-title"]/div[@class="main"]/h1/text()').extract()
        if title:
            title = title[0]
        else:
            title = response.xpath('//section[@id="s-title"]/div[@class="main"]/h1/text()')
            if title:
                title = title[0].replace(u' - 天猫Tmall.com', '')
            else:
                title = ''

        # category of item
        if 'valItemInfo' in data_detail_js.keys() and 'skuList' in data_detail_js['valItemInfo'].keys():
            skuList = data_detail_js.get('valItemInfo').get('skuList')
            names_dict = dict()
            for sku in skuList:
                skuid = sku.get('skuId', None)
                names = sku.get('names', None)
                names_dict[skuid] = names

        # 优惠活动
        youhui = []
        if 'defaultModel' in data_mdskip_js.keys() and 'couponDataDo' in data_mdskip_js[
            'defaultModel'].keys() and 'couponList' in data_mdskip_js[
            'defaultModel']['couponDataDo'].keys():
            for one in data_mdskip_js['defaultModel']['couponDataDo']['couponList']:
                if 'title' in one.keys() and one['title'] != '领取优惠券':
                    youhui.append(one['title'])
            youhui = ';'.join(youhui)
            youhui = youhui.replace('.', '点')

        elif 'defaultModel' in data_mdskip_js.keys() and 'itemPriceResultDO' in data_mdskip_js[
            'defaultModel'].keys() and 'tmallShopProm' in \
                data_mdskip_js['defaultModel']['itemPriceResultDO'].keys():
            for one in data_mdskip_js['defaultModel']['itemPriceResultDO']['tmallShopProm']:
                if 'promPlanMsg' in one.keys():
                    youhui = ';'.join(one['promPlanMsg'])
                    youhui = youhui.replace('.', '点')

        # 以上为不同颜色/型号商品共享的数据，以下求每个颜色/型号的商品信息
        if 'defaultModel' in data_mdskip_js.keys() and 'itemPriceResultDO' in data_mdskip_js[
            'defaultModel'].keys() and 'priceInfo' in data_mdskip_js[
            'defaultModel']['itemPriceResultDO'].keys():
            # 本店活动
            if 'tmallShopProm' in data_mdskip_js['defaultModel']['itemPriceResultDO']:
                for a in data_mdskip_js['defaultModel']['itemPriceResultDO']['tmallShopProm']:
                    msg = a['promPlan'][0].values()[0]
            else:
                msg = ''
            for elem in data_mdskip_js['defaultModel']['itemPriceResultDO']['priceInfo'].keys():

                value = data_mdskip_js['defaultModel']['itemPriceResultDO']['priceInfo'][elem]
                temp = {'_id': 'https://detail.tmall.com/item.htm?id=%s&skuId=%s' % ('12345', elem)}
                if youhui:
                    temp['优惠活动'] = youhui
                if 'tagPrice' in value.keys() and len(value['tagPrice']) > 0:
                    temp['原价'] = value['tagPrice']
                elif 'price' in value.keys() and len(value['price']) > 0:
                    temp['原价'] = value['price']
                if 'promotionList' in value.keys():
                    for one in value['promotionList']:
                        if 'price' in one.keys() and len(one['price']) > 0:
                            temp['现价'] = one['price']

                        if 'startTime' in one.keys():
                            temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(one['startTime'] / 1000))
                        elif 'tradeResult' in data_mdskip_js['defaultModel'].keys() and 'startTime' in \
                                data_mdskip_js['defaultModel'][
                                    'tradeResult'].keys():
                            startTime = data_mdskip_js['defaultModel']['tradeResult']['startTime']
                            temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(startTime / 1000))
                        if 'endTime' in one.keys():
                            temp['活动结束时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(one['endTime'] / 1000))
                        temp['活动'] = msg

                        item = TmallItem()
                        for a_item in item.fields:
                            item[a_item] = ''
                        item['prodId'] = response.meta['id']
                        item['skuid'] = elem
                        item['type'] = names_dict[elem]
                        item['title'] = title
                        item['start_time'] = temp['活动开始时间']
                        item['youhui'] = temp['优惠活动']
                        item['huodong'] = temp['活动']
                        item['yuanjia'] = temp['原价']
                        item['xianjia'] = temp['现价']
                        item['end_time'] = temp['活动结束时间']
                        # yield item
                        # print names_dict
                        print item
