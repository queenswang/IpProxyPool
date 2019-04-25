from multiprocessing import Value, Queue, Process
from config import config
from spider.HtmlCrawl import IpCrawl
from usable.usable import usable
from db.db_select import save_data

def startProxyCrawl(queue,db_proxy_num):
    crawl = IpCrawl(queue,db_proxy_num)
    crawl.run()

def validator(queue1,queue2):
    pass

if __name__ == "__main__":
    DB_PROXY_NUM = Value('i', 0)
    q1 = Queue(maxsize=config.TASK_QUEUE_SIZE)
    q2 = Queue()
    p1 = Process(target=startProxyCrawl, args=(q1, DB_PROXY_NUM))
    p2 = Process(target=usable, args=(q1, q2))
    p3 = Process(target=save_data, args=(q2, DB_PROXY_NUM))
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()