# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi
from .items import *


class TmallPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool
        # self.file = open('document','wb')

    @classmethod
    def from_settings(cls, settings):
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            port=settings['MYSQL_PORT'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    def process_item(self, item, spider):
        d = self.dbpool.runInteraction(self._do_upinsert, item, spider)
        return item

    def _do_upinsert(self, conn, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                print 'NOT ANY DATA IN ITEM'
        if valid:
            if isinstance(item, TmallItem):
                mysql = "INSERT IGNORE INTO `jiafang_tianmao`(" \
                        "`prodId`," \
                        "`type`," \
                        "`youhui`," \
                        " `huodong`, " \
                        " `yuanjia`, " \
                        " `xianjia`, " \
                        " `start_time`, " \
                        " `end_time`, " \
                        " `title`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                result = conn.execute(mysql,
                                      (item['prodId'],
                                       item['type'],
                                       item['youhui'],
                                       item['huodong'],
                                       item['yuanjia'],
                                       item['xianjia'],
                                       item['start_time'],
                                       item['end_time'],
                                       item['title']
                                       ))
                if result:
                    print 'added a record'
                else:
                    print 'failed insert into table `jiafang_tianmao`'
            else:
                mysql = "INSERT IGNORE INTO `jiafang_tianmao_reviews`(" \
                        "`prodId`," \
                        "`name`," \
                        "`date`," \
                        " `content`) values(%s,%s,%s,%s)"
                result = conn.execute(mysql,
                                      (item['prodId'],
                                       item['name'],
                                       item['date'],
                                       item['content']
                                       ))
                if result:
                    print 'added a record'
                else:
                    print 'failed insert into table `jiafang_tianmao_reviews`'

