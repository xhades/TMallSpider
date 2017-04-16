# !/usr/bin/env python
# encoding=utf-8

"""
@author: xhades
@Date: 2017/4/11

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
from TMall.items import TmallItem


class TmallSpider(CrawlSpider):
    name = 'mt'

    def __init__(self):
        super(TmallSpider, self).__init__()
        self.allowed_domains = ['https://meizhuang.tmall.com/?spm=a220o.1000855.0.0.KrkEU0']
        self.start_urls = ['https://www.tmall.com/?spm=a2233.7711963.a2226n0.1.Q4u4Us']
        self.itemid='21479223750'

        # items xpath
        self.simpleIntroduction_xpath = "//div[@class='tb-detail-hd']/h1"
        self.price_xpath = "//span[@class='tm-price']"

        # customer_reviews settings
        self.start_page = 1
        self.end_page = 1

    @staticmethod
    def get_name():
        pass


    def parse(self, response):
        logging.info("=====GET SUCCESS=======")
        url = "https://detail.m.tmall.com/item.htm?id={}".format(self.itemid)
        yield scrapy.Request(url, dont_filter=True, callback=self.parse_item)

    def parse_item(self, response):
        logging.info("=====START PARSER ITEM=======")
        data_detail = re.findall('_DATA_Detail = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_mdskip = re.findall('_DATA_Mdskip = *?\n?(.*?\});? ?\n', response.body.decode('gbk'))
        data_detail_js = json.loads(data_detail[0])
        data_mdskip_js = json.loads(data_mdskip[0])
        # print data_detail_js['skuList']
        # print data_mdskip_js

        html = response.body.decode('gbk', 'ignore')
        title = response.xpath('//section[@id="s-title"]/div[@class="main"]/h1/text()').extract()[0]
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
            # print skuList
            for sku in skuList:
                names = sku.get('names', None)
            for key in data_detail_js['valItemInfo']['skuPics'].keys():
                try:
                    value = data_detail_js['valItemInfo']['skuPics'][key]
                    # if key.startswith(';'):
                    #     key = key[1:]
                    # if key.endswith(';'):
                    #     key = key[:-1]
                    # key = 'https://detail.tmall.com/item.htm?id=%s&sku_properties=%s' % (
                    #     routine['_id'], key.replace(';', '&'))
                    # if value.startswith('//'):
                    #     value = 'http:' + value
                    # elif value.startswith('/'):
                    #     value = 'http:/' + value
                    # elif not value.startswith('http'):
                    #     value = 'http://' + value
                    # img_routines.append({'_id': value, '商品链接': key, '商品标题': title})
                    # print value
                except Exception, e:
                    print e

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
                if 'suggestivePromotionList' in value.keys():
                    for one in value['suggestivePromotionList']:
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
                        print '-'*40
                        print temp['活动开始时间'], temp['优惠活动'],temp['活动'], temp['原价'], temp['现价'], temp['活动结束时间']


    #     print response.body.decode('gbk').encode('utf8')
    #
    #     item = TmallItem()
    #     for a_item in item.fields:
    #         item[a_item] = ''
    #     try:
    #         item['price'] = response.xpath(self.price_xpath).xpath("string(.)").extract()[-1].encode('utf-8')
    #     except:
    #         item['price'] = ''
    #
    #     try:
    #         item['simpleIntroduction'] = response.xpath(self.simpleIntroduction_xpath).xpath("string(.)").extract()[0].replace("\n","").replace("\t","").strip().encode('utf-8')
    #     except:
    #         item['simpleIntroduction'] = ''
    #
    #
    #     item['url'] = response.url
    #
    #     yield item
    #
    #     # define no of page turn to get customer_reviews
    #     # 20 customer_reviews of per page
    #     for page in xrange(self.start_page, self.end_page+1):
    #         itemid=self.itemid
    #         spuid= re.search("spuId=(\d+)", response.body).group(1)
    #         sellerid= re.search("sellerId=(\d+)", response.body).group(1)
    #         reviews_url = "https://rate.tmall.com/list_detail_rate.htm?itemId={}&spuId={}&sellerId={}&order=3&currentPage={}".format(itemid,spuid,sellerid,page)
    #         headers = {
    #             ':authority': 'rate.tmall.com',
    #             ':scheme': 'https',
    #             'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
    #         }
    #         yield scrapy.Request(reviews_url, callback=self.parse_reviews, dont_filter=True, meta={'item':item})
    #
    # def parse_reviews(self, response):
    #     logging.info("=====Start Get Reviews=======")
    #     item = response.meta['item']
    #     content = response.body
    #     nickname = []
    #     ratedate = []
    #     ratecontent = []
    #     nickname.extend(re.findall('"displayUserNick":"(.*?)"',content))
    #     ratecontent.extend(re.findall(re.compile('"rateContent":"(.*?)","rateDate"'), content))
    #     ratedate.extend(re.findall(re.compile('"rateDate":"(.*?)","reply"'), content))
    #     for i in list(range(0, len(nickname))):
    #         with open('{}.csv'.format(item['simpleIntroduction']), 'a') as f:
    #             f.write(','.join((nickname[i], ratedate[i], ratecontent[i])) + '\n')
    #
    #     # print item
    #     for k,v in item.items():
    #         print k, ': ', v



