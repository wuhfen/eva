# coding:utf-8
import mysql.connector
from subprocess import Popen,PIPE


def mysql_alive(host,password,user='root',port='3306',database='mysql'):
    try:
        conn = mysql.connector.connect(host=host,port=port,user=user,password=password,database=database)
        conn.close()
        alive=True
    except:
        alive=False
    return alive



def execute_sqlfile(host,port,user,password,path,filename):
    '''内部调用不用那么严谨，如果是多人合作开发，这个函数需要做参数类型，参数个数，参数格式的判断，提供报错信息'''
    args=['mysql', '-h', host, '-P', port, '-u', user, '--password=' + password]
    proc = Popen(args,stdout=PIPE, stdin=PIPE,stderr=PIPE,cwd=path)
    out,err = proc.communicate('source ' + filename)
    if not out: out = ""
    if not err: err = ""
    return {"out":out,"err":err}
