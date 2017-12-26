#!/usr/bin/env python
# coding:utf-8

import paramiko
from assets.models import Server
import socket  #导入socket模块

def ssh_cmd(host,commands):
    print "host="+host
    #主机可以连通在调用此函数
    host_obj = Server.objects.get(ssh_host=host)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, host_obj.ssh_port, host_obj.ssh_user,host_obj.ssh_password)
    stdin, stdout, stderr = ssh.exec_command(commands,timeout=None)
    res = stdout.readlines()
    ssh.close()
    return res

def ssh_check(host): 
    #检查主机是否可用的函数
    host_obj = Server.objects.get(ssh_host=host)
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(1)
    try:
        sk.connect((host,host_obj.ssh_port))
        ok = True
    except:
        ok = False
    sk.close()
    return ok