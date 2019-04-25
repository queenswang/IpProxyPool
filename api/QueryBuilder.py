from db.db_select import sqlhelper
from db.models import Proxy

class Inquire():
    def __init__(self,count,conditions,db):
        self.proxys = []
        self.count = count
        self.conditions = conditions

    def quire(self):
        self.proxys = sqlhelper.select(count=self.count, conditions=self.conditions)
        return self.proxys