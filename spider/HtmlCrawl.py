from config import config
import sys
import time
import gevent
from gevent import monkey
monkey.patch_all()

from gevent.pool import Pool
from multiprocessing import Queue,Process
from db.db_select import sqlhelper
from usable.usable import detect_from_db
from spider.HtmlDownloader import Downloader
from spider.HtmlParser import Parser

class IpCrawl(object):
    proxies = set()

    def __init__(self, queue, db_proxy_num):
        self.pool = Pool(config.THREADNUM)
        self.queue = queue
        self.db_proxy_num = db_proxy_num

    def run(self):
        while True:
            self.proxies.clear()
            str = 'IpProxyPool----->>>>>>>>beginning'
            sys.stdout.write(str + "\r\n")
            sys.stdout.flush()
            # 获取当前所有代理ip，进行测试是否可用
            proxylist = sqlhelper.select()

            for proxy in proxylist:
                self.pool.spawn(detect_from_db, proxy, self.proxies)
            self.pool.join()
            self.db_proxy_num.value = len(self.proxies)
            str = 'IPProxyPool----->>>>>>>>db exists ip:%d' % len(self.proxies)

            # 可用库存太少时，需要重新爬取代理ip
            if len(self.proxies) < config.MINNUM:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()

                for p in config.PARSELIST:
                    self.pool.spawn(self.crawl, p)
                self.pool.join()
            else:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num meet the requirement,wait UPDATE_TIME...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()

            # time.sleep(config.UPDATE_TIME)

    def crawl(self, parser):
        html_parser = Parser()
        for url in parser['urls']:
            print("download:{}".format(url))
            response = Downloader.download(url)
            if response is not None:
                print("开始解析网站{}".format(url))
                proxylist = html_parser.parse(response, parser)
                print("获取代理列表：{}".format(proxylist))
                if proxylist is not None:
                    for proxy in proxylist:
                        proxy_str = '{}:{}'.format(proxy['ip'], proxy['port'])
                        if proxy_str not in self.proxies:
                            self.proxies.add(proxy_str)
                            while True:
                                if self.queue.full():
                                    time.sleep(0.1)
                                else:
                                    self.queue.put(proxy)
                                    break
