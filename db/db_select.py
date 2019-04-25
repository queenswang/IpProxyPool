from util.exceptions import Con_DB_Fail
from config import config
from flask_sqlalchemy import SQLAlchemy
import sys

db_config = config.DB_CONNECT_TYPE
try:
    if db_config == "mongodb":
        from db.db_mongo import SqlSelector
    elif db_config == "redis":
        from db.db_redis import SqlSelector
    elif db_config == "sqlite":
        from db.db_sqlite import SqlSelector
    else:
        from db.db_mysql import SqlSelector
    sqlhelper =  SqlSelector()
except:
    raise Con_DB_Fail(db_config)



def connect_mysql(app):
    return SQLAlchemy(app)

def save_data(queue,db_proxy_num):
    '''
    :param queue: 可用的代理ip
    :param db_proxy_num: 代理ip数量
    :return:
    '''
    successNum = 0
    failNum = 0
    while True:
        try:
            proxy = queue.get(timeout=300)
            if proxy:
                sqlhelper.insert(proxy)
                successNum += 1
            else:
                failNum += 1
            str = 'IPProxyPool----->>>>>>>>Success ip num :%d,Fail ip num:%d' % (successNum, failNum)
            sys.stdout.write(str + "\r")
            sys.stdout.flush()
        except BaseException as e:
            if db_proxy_num.value != 0:
                successNum += db_proxy_num.value
                db_proxy_num.value = 0
                str = 'IPProxyPool----->>>>>>>>Success ip num :%d,Fail ip num:%d' % (successNum, failNum)
                sys.stdout.write(str + "\r")
                sys.stdout.flush()
                successNum = 0
                failNum = 0