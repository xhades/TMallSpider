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
import re
from TMall.items import TmallItem, TmallReviewsItem


class TmallSpider(CrawlSpider):
    name = 'boyang'
    custom_settings = {'ITEM_PIPELINES': {'TMall.pipelines.TmallPipeline': 300}}

    def __init__(self):
        super(TmallSpider, self).__init__()
        self.allowed_domains = ['https://www.tmall.com/']
        self.start_urls = ['https://beyond.tmall.com/']

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
            url = 'https://beyond.tmall.com/i/asynSearch.htm?_ksTS=1496241869905_136&callback=jsonp137&mid=w-14593672890-0&wid=14593672890&path=/category.htm&&spm=a1z10.5-b-s.w4011-14593672890.402.8G2yjX&pageNo={}'.format(page)
            yield scrapy.Request(url, callback=self.parse_page, dont_filter=True)

    def parse_page(self, response):
        logging.info("=====PARSE NEXT PAGE=======")

        href_list = response.xpath("//a[contains(@class, 'J_TGoldData')]").extract()

        id_list = [re.search("id=(\d+)&", href).group(1) for href in href_list]
        for id in id_list:
            url = "https://detail.m.tmall.com/item.htm?id={}".format(id)
            yield scrapy.Request(url, dont_filter=True, callback=self.parse_item, meta={'id':id})

    def parse_item(self, response):

        logging.info("=====START PARSER ITEM=======")
        data_detail = re.findall('_DATA_Detail = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_mdskip = re.findall('_DATA_Mdskip = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_detail_js = json.loads(data_detail[0])
        data_mdskip_js = json.loads(data_mdskip[0])

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
            skuName = data_detail_js.get('valItemInfo').get('skuName')

            names_dict = dict()
            for sku in skuList:
                skuid = sku.get('skuId', None)
                # names = sku.get('names', None)
                pvs = sku.get('pvs', None)
                pvs_data = pvs.split(";")

                a_k = pvs_data[0].split(":")[0]
                a_val = pvs_data[0].split(":")[-1]

                b_k = pvs_data[-1].split(":")[0]
                b_val = pvs_data[-1].split(":")[-1]

                colors = filter(lambda item: item.get('id') == a_k, skuName)[0].get("values", '')
                color = filter(lambda item: item.get("id") == a_val, colors)[0].get("text")
                types = filter(lambda item: item.get('id') == b_k, skuName)[0].get("values", '')
                type = filter(lambda item: item.get("id") == b_val, types)[0].get("text")

                names_dict[skuid] = color+type

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
        # 销量
        sellcount = data_mdskip_js['defaultModel']['sellCountDO'].get('sellCount', 'not got sellcount')

        # 库存
        quantity_dict = dict()
        skuQuantitys = data_mdskip_js['defaultModel']['inventoryDO'].get('skuQuantity')
        for k, v in skuQuantitys.items():
           quantity_dict[k] = v.get('quantity', 'Not got')

        # 以上为不同颜色/型号商品共享的数据，以下求每个颜色/型号的商品信息
        if 'defaultModel' in data_mdskip_js.keys() and 'itemPriceResultDO' in data_mdskip_js[
            'defaultModel'].keys() and 'priceInfo' in data_mdskip_js[
            'defaultModel']['itemPriceResultDO'].keys():

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
                        # if 'startTime' in one.keys():
                        #     temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                        #                                    time.localtime(one['startTime'] / 1000))
                        # elif 'tradeResult' in data_mdskip_js['defaultModel'].keys() and 'startTime' in \
                        #         data_mdskip_js['defaultModel'][
                        #             'tradeResult'].keys():
                        #     startTime = data_mdskip_js['defaultModel']['tradeResult']['startTime']
                        #     temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                        #                                    time.localtime(startTime / 1000))
                        if 'endTime' in one.keys():
                            temp['活动结束时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(one['endTime'] / 1000))

                        if 'type' in one.keys() and 'status' in one.keys():
                            if one['status'] == 1:

                                temp['huodong'] = one['type']
                            else:
                                temp['huodong'] = ''

                        item = TmallItem()
                        for a_item in item.fields:
                            item[a_item] = ''
                        item['prodId'] = response.meta['id']
                        item['skuid'] = elem
                        item['type'] = names_dict[elem]
                        item['sellcount'] = sellcount
                        item['title'] = title
                        # item['start_time'] = temp['活动开始时间']
                        item['youhui'] = temp['优惠活动']
                        item['yuanjia'] = temp['原价']
                        item['xianjia'] = temp['现价']
                        item['kucun'] = quantity_dict[elem]
                        item['huodong'] = temp['huodong'] + u"活动结束时间:" + temp['活动结束时间']

                        item['dianpu'] = u"博洋"
                        yield item
                        # print item

                elif 'suggestivePromotionList' in value.keys():
                    for one in value['suggestivePromotionList']:
                        if 'price' in one.keys() and len(one['price']) > 0:
                            temp['现价'] = one['price']

                        # if 'startTime' in one.keys():
                        #     temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                        #                                    time.localtime(one['startTime'] / 1000))
                        #
                        # elif 'tradeResult' in data_mdskip_js['defaultModel'].keys() and 'startTime' in \
                        #         data_mdskip_js['defaultModel'][
                        #             'tradeResult'].keys():
                        #     startTime = data_mdskip_js['defaultModel']['tradeResult']['startTime']
                        #     temp['活动开始时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                        #                                    time.localtime(startTime / 1000))
                        if 'endTime' in one.keys():
                            temp['活动结束时间'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                           time.localtime(one['endTime'] / 1000))

                        if 'type' in one.keys() and 'status' in one.keys():
                            if one['status'] == 1:
                                temp['huodong'] = one['type']
                            else:
                                temp['huodong'] = ''

                        item = TmallItem()
                        for a_item in item.fields:
                            item[a_item] = ''
                        item['prodId'] = response.meta['id']
                        item['skuid'] = elem
                        item['type'] = names_dict[elem]
                        item['sellcount'] = sellcount
                        item['title'] = title
                        # item['start_time'] = temp['活动开始时间']
                        item['youhui'] = temp['优惠活动']
                        item['yuanjia'] = temp['原价']
                        item['xianjia'] = temp['现价']
                        item['kucun'] = quantity_dict[elem]
                        item['huodong'] = temp['huodong'] + u"活动结束时间:" + temp['活动结束时间']
                        item['dianpu'] = u"博洋"
                        # item['end_time'] = temp['活动结束时间']
                        yield item
                        # print item
