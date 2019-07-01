#!/usr/bin/env python
# coding:utf-8

import paramiko
from assets.models import Server
import socket  #导入socket模块
import sys

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
    #检查主机是否可用的
    try:
        host_obj = Server.objects.get(ssh_host=host)
    except:
        host_obj = Server.objects.filter(ssh_host=host)[0]
    sk = paramiko.SSHClient()
    sk.load_system_host_keys()
    sk.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        sk.connect(host,int(host_obj.ssh_port),username=host_obj.ssh_user,password=host_obj.ssh_password)
        ok = True
        sk.close()
    except:
        ok = False
    return ok

def run_cmd(host,port,password,user,cmd):
    port = int(port)
    print "----------->> %s"% host
    s = paramiko.SSHClient()
    s.load_system_host_keys()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    res=[]

    try:
        s.connect(host, port, username=user, password=password, timeout=5)
    except OSError:
        print "Port Error: %s %s"% (host,port)
        res.append(u"Port Error: %s %s\n"% (host,port))
        if port=='22':
            port='22992'
        else:
            port='22'
        print "Change Port And Reconnect %s "% port
        try:
            s.connect(host, port, username=user, password=password, timeout=5)
            res.append(u"Port success: %s %s\n" % (host, port))
            print "Port success: %s %s\n" % (host, port)
        except:
            print "Host failure %s"% host
    except paramiko.AuthenticationException:
        print "Password Error"
        res.append(u"Password Error %s\n"% host)
    except paramiko.SSHException:
        print "Maybe the system is windows"
        res.append(u"Host is Windows %s\n" % host)
    else:
        print "Connect Success"

    stdin, stdout, stderr = s.exec_command(cmd,timeout=30,get_pty=True)
    cmd_result = stdout.read()
    s.close()
    print "<<-----------"
    return cmd_result


def run_ftp(host,port,password,user,filepath,remotefile):
    port = int(port)
    t = paramiko.Transport((host, port))
    print "------->>%s"% host
    try:
        t.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(filepath, remotefile)
        t.close()
        print 'upload file %s success'% remotefile
    except:
        print "host %s failure"% host
    print "<<--------"