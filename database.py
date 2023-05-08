import pymysql


def getconnect():
    connect = pymysql.connect(host='localhost', user='root', password='zrl20040103', database='stock', charset='utf8')
    return connect


def closeconnect(connect):
    connect.close()


def executesql(sql, **args):
    connect = getconnect()
    with connect.cursor() as cursor:
        result = cursor.execute(sql, args)
        if sql.startswith('select'):
            result = cursor.fetchall()
    connect.commit()
    closeconnect(connect)
    return result
