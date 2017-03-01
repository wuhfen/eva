#!/usr/bin/env python
# coding:utf-8

import paramiko
from assets.models import Server

def ssh_cmd(host,commands):
    host_obj = Server.objects.get(ssh_host=host)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, host_obj.ssh_port, host_obj.ssh_user,host_obj.ssh_password)
    stdin, stdout, stderr = ssh.exec_command(commands,timeout=20)
    res = stdout.readlines()
    ssh.close()
    return res