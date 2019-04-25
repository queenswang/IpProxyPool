from config import config
import random
import requests
import chardet
from db.db_select import sqlhelper

import threading
lock = threading.Lock()

class Downloader(object):

    @staticmethod
    def download(url):
        try:
            r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
            r.encoding = chardet.detect(r.content)['encoding']
            if (not r.ok) or len(r.content) < 500:
                raise ConnectionError
            else:
                return r.text

        except:
            count = 0  # 重试次数
            lock.acquire()
            proxylist = sqlhelper.select(10)
            lock.release()
            if not proxylist:
                return None

            while count < config.RETRY_TIME:
                try:
                    proxy = random.choice(proxylist)
                    ip = proxy[0]
                    port = proxy[1]
                    proxies = {"http": "http://{}:{}".format(ip, port), "https": "http://{}:{}".format(ip, port)}

                    r = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
                    r.encoding = chardet.detect(r.content)['encoding']
                    if (not r.ok) or len(r.content) < 500:
                        raise ConnectionError
                    else:
                        return r.text
                except:
                    count += 1

        return None