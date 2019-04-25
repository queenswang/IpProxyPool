class Test_URL_Fail(Exception):
    def __init__(self,str):
        self.str = str
    def __str__(self):
        str = "访问{}失败，请检查网络连接".format(self.str)
        return str


class Con_DB_Fail(Exception):
    def __init__(self,str):
        self.str = str
    def __str__(self):
        str = "使用DB_CONNECT_STRING:{}--连接数据库失败".format(self.str)
        return str