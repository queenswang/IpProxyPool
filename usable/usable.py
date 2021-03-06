import sys
from config import config
import time
import requests
import json
from db.db_select import sqlhelper
from multiprocessing import Process, Queue
import psutil
import os
import gevent
from gevent import monkey
monkey.patch_all()
import threading
lock = threading.Lock()

import chardet


def usable(queue1, queue2):
    tasklist = []
    proc_pool = {}  # 所有进程列表
    cntl_q = Queue()  # 控制信息队列
    while True:
        if not cntl_q.empty():
            # 处理已结束的进程
            try:
                pid = cntl_q.get()
                proc = proc_pool.pop(pid)
                proc_ps = psutil.Process(pid)
                proc_ps.kill()
                proc_ps.wait()
            except Exception as e:
                pass
                # print(e)
                # print(" we are unable to kill pid:%s" % (pid))
        try:
            # proxy_dict = {'source':'crawl','data':proxy}
            if len(proc_pool) >= config.MAX_CHECK_PROCESS:
                time.sleep(config.CHECK_WATI_TIME)
                continue
            proxy = queue1.get()
            tasklist.append(proxy)
            if len(tasklist) >= config.MAX_CHECK_CONCURRENT_PER_PROCESS:
                p = Process(target=process_start, args=(tasklist, queue2, cntl_q))
                p.start()
                proc_pool[p.pid] = p
                tasklist = []

        except Exception as e:
            if len(tasklist) > 0:
                p = Process(target=process_start, args=(tasklist, queue2, cntl_q))
                p.start()
                proc_pool[p.pid] = p
                tasklist = []

def process_start(tasks, queue2, cntl):
    spawns = []
    for task in tasks:
        spawns.append(gevent.spawn(detect_proxy, task, queue2))
    gevent.joinall(spawns)
    cntl.put(os.getpid())  # 子进程退出是加入控制队列

def detect_from_db(proxy, proxies_set):
    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    result = detect_proxy(proxy_dict)

    if result:
        proxy_str = '{}:{}'.format(proxy[0], proxy[1])
        proxies_set.add(proxy_str)

    else:
        if proxy[2] < 1:
            lock.acquire()
            sqlhelper.delete({'ip': proxy[0], 'port': proxy[1]})
            lock.release()
        else:
            score = proxy[2]-1
            lock.acquire()
            sqlhelper.update({'ip': proxy[0], 'port': proxy[1]}, {'score': score})
            lock.release()
            proxy_str = '{}:{}'.format(proxy[0], proxy[1])
            proxies_set.add(proxy_str)

def detect_proxy(proxy, queue2=None):
    '''
    :param proxy: ip字典
    :return:
    '''
    ip = proxy['ip']
    port = proxy['port']
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "https://%s:%s" % (ip, port)}
    protocol, types, speed = getattr(sys.modules[__name__],config.CHECK_PROXY)(proxies)
    if protocol >= 0:
        proxy['protocol'] = protocol
        proxy['types'] = types
        proxy['speed'] = speed
    else:
        proxy = None
    if queue2:
        queue2.put(proxy)
    return proxy

def checkProxy(proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    :param
    :return:
    '''
    protocol = -1
    types = -1
    speed = -1
    http, http_types, http_speed = _checkHttpProxy(proxies)
    https, https_types, https_speed = _checkHttpProxy(proxies, False)
    if http and https:
        protocol = 2
        types = http_types
        speed = http_speed
    elif http:
        types = http_types
        protocol = 0
        speed = http_speed
    elif https:
        types = https_types
        protocol = 1
        speed = https_speed
    else:
        types = -1
        protocol = -1
        speed = -1
    return protocol, types, speed


def _checkHttpProxy(proxies, isHttp=True):
    types = -1
    speed = -1
    if isHttp:
        test_url = config.TEST_HTTP_HEADER
    else:
        test_url = config.TEST_HTTPS_HEADER
    try:
        start = time.time()
        r = requests.get(url=test_url, headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        print("使用代理{}访问{}".format(proxies,test_url))
        if r.ok:
            speed = round(time.time() - start, 2)
            content = json.loads(r.text)
            headers = content['headers']
            ip = content['origin']
            proxy_connection = headers.get('Proxy-Connection', None)
            if ',' in ip:
                types = 2
            elif proxy_connection:
                types = 1
            else:
                types = 0

            return True, types, speed
        else:
            return False, types, speed
    except Exception as e:
        return False, types, speed

def baidu_check(proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    :param
    :return:
    '''
    protocol = -1
    types = -1
    speed = -1
    # try:
    #     #http://ip.chinaz.com/getip.aspx挺稳定，可以用来检测ip
    #     r = requests.get(url=config.TEST_URL, headers=config.get_header(), timeout=config.TIMEOUT,
    #                      proxies=proxies)
    #     r.encoding = chardet.detect(r.content)['encoding']
    #     if r.ok:
    #         if r.text.find(selfip)>0:
    #             return protocol, types, speed
    #     else:
    #         return protocol,types,speed
    #
    #
    # except Exception as e:
    #     return protocol, types, speed
    try:
        start = time.time()
        r = requests.get(url='https://www.baidu.com', headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        print("使用代理{}访问百度：".format(proxies, r.status_code))
        r.encoding = chardet.detect(r.content)['encoding']
        if r.ok:
            speed = round(time.time() - start, 2)
            protocol= 0
            types=0

        else:
            speed = -1
            protocol= -1
            types=-1
    except Exception as e:
            speed = -1
            protocol = -1
            types = -1
    return protocol, types, speed

def taobao_check(proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    :param
    :return:
    '''
    protocol = -1
    types = -1
    speed = -1
    # try:
    #     #http://ip.chinaz.com/getip.aspx挺稳定，可以用来检测ip
    #     r = requests.get(url=config.TEST_URL, headers=config.get_header(), timeout=config.TIMEOUT,
    #                      proxies=proxies)
    #     r.encoding = chardet.detect(r.content)['encoding']
    #     if r.ok:
    #         if r.text.find(selfip)>0:
    #             return protocol, types, speed
    #     else:
    #         return protocol,types,speed
    #
    #
    # except Exception as e:
    #     return protocol, types, speed
    try:
        start = time.time()
        r = requests.get(url='https://www.taobao.com', headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        print("使用代理{}访问淘宝：{}".format(proxies, r.status_code))
        r.encoding = chardet.detect(r.content)['encoding']
        if r.ok:
            speed = round(time.time() - start, 2)
            protocol= 0
            types=0

        else:
            speed = -1
            protocol= -1
            types=-1
    except Exception as e:
            speed = -1
            protocol = -1
            types = -1
    return protocol, types, speed