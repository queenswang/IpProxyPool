from db.ISqlHelper import ISqlHelper
from db.models import  Proxy, BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config

import pymysql
pymysql.install_as_MySQLdb()

class SqlSelector(ISqlHelper):
    params = {'ip': Proxy.ip, 'port': Proxy.port, 'types': Proxy.types, 'protocol': Proxy.protocol,
              'country': Proxy.country, 'area': Proxy.area, 'score': Proxy.score}
    def __init__(self,db=None):
        if db is not None:
            # flask 连接 mysql
            self.mode = "online"
            self.db = db
            self.session = db.session
        else:
            # flask 服务没开时使用
            self.mode = "offline"
            self.db = create_engine(config.SQLALCHEMY_DATABASE_URI)
            DB_session = sessionmaker(bind=self.db)
            self.session = DB_session()

    def init_db(self):
        # 创建表
        if self.mode == "online":
            self.db.create_all()
        else:
            BaseModel.metadata.create_all(self.db)

    def drop_db(self):
        # 删除表
        if self.mode == "online":
            self.db.drop_all()
        else:
            BaseModel.metadata.drop_all(self.db)

    def insert(self, value):
        # 插入
        proxy = Proxy(ip=value['ip'], port=value['port'], types=value['types'], protocol=value['protocol'],
                      country=value['country'],
                      area=value['area'], speed=value['speed'])
        self.session.add(proxy)
        self.session.commit()

    def delete(self, conditions=None):
        # 删除
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            deleteNum = query.delete()
            self.session.commit()
        else:
            deleteNum = 0
        return {'deleteNum', deleteNum}

    def update(self, conditions=None, value=None):
        ''' 更新
        :param conditions: 格式是个字典。类似self.params
        :param value:也是个字典：{'ip':192.168.0.1}
        :return:
        '''
        if conditions and value:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            updatevalue = {}
            for key in list(value.keys()):
                if self.params.get(key, None):
                    updatevalue[self.params.get(key, None)] = value.get(key)
            updateNum = query.update(updatevalue)
            self.session.commit()
        else:
            updateNum = 0
        return {'updateNum': updateNum}


    def select(self, count=None, conditions=None):
        '''
        :param count: 返回记录条数
        :param conditions: 查询条件，是个字典。类似self.params
        :return: 查询到的记录
        '''
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
        else:
            conditions = []

        query = self.session.query(Proxy.ip, Proxy.port, Proxy.score)
        if len(conditions) > 0 and count:
            for condition in conditions:
                query = query.filter(condition)
            return query.order_by(Proxy.score.desc(), Proxy.speed).limit(count).all()
        elif count:
            return query.order_by(Proxy.score.desc(), Proxy.speed).limit(count).all()
        elif len(conditions) > 0:
            for condition in conditions:
                query = query.filter(condition)
            return query.order_by(Proxy.score.desc(), Proxy.speed).all()
        else:
            return query.order_by(Proxy.score.desc(), Proxy.speed).all()


    def close(self):
        pass

if __name__ == "__main__":
    # sqlselector = SqlSelector()
    # sqlselector.delete({"ip":"127.0.0.1"})
    pass