# -*- coding:utf-8 -*-

from config import config
from flask import Flask, request, jsonify
from db.db_select import connect_mysql
from db.db_mysql import SqlSelector
from api.QueryBuilder import Inquire
import pymysql
pymysql.install_as_MySQLdb()

# 注册主app
IpProxyPool = Flask(__name__)

# 加载配置文件
IpProxyPool.config.from_object(config)

# 链接数据库
db = connect_mysql(IpProxyPool)

# /proxy?count=5&types=0&country=0&area=xx&protocol=0
@IpProxyPool.route("/proxy",methods=["GET"])
def request_proxy():
    types = request.args.get("types")
    count = request.args.get("count")
    country = request.args.get("country")
    area = request.args.get("area")

    conditions = {}
    if not count or int(count) < 1:
        count = 1

    if not types:
        types = 0

    conditions["types"] = int(types)
    if country is not None:
        conditions["country"] = country
    if area is not None:
        conditions["area"] = area

    inquire = Inquire(count,conditions,db)
    proxys = inquire.quire()  # 返回一个列表，列表元素格式为 [ip,port,score]
    msg = ""
    if len(proxys) > 0:
        status = "Success"
        msg = "查到 {} 条代理ip".format(len(proxys))
    else:
        status = "Faild"
        msg = "查询失败"
    data = {
        "status": status,
        "msg":msg,
        "proxys":proxys
    }
    return jsonify(data)


if __name__ == "__main__":
    IpProxyPool.run(debug=True)
