#!/data/myproject/venv/bin/python
#-*- encoding: utf-8 -*-
#########################################################################
# File Name: deploy.py
# Author: wuhf
# Email: admin#dwhd.org
# Version:
# Created Time: 2016年12月07日 星期三 13时01分02秒
#########################################################################

import subprocess
import os

# 脚本放在/data/myproject下面运行，可以更新版本

git_address = "https://github.com/wuhfen/eva.git"
cmd = '''ls |awk -F'_' '/cmdb_/{print $NF}'
'''

p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
result = p.stdout.readlines()
L = [int(a.strip("\n")) for a in result if a]
#print result
print L
#print max(tuple(L))
max_num = max(L)

print max_num
new_num = int(max_num) + 1
dir_name = "cmdb_" + str(new_num)

git_clone = '''git clone %s %s''' % (git_address,dir_name)

a = subprocess.Popen(git_clone,shell=True)
a.wait()
b = subprocess.Popen(['rm -f cmdb'],shell=True)
b.wait()
c = os.symlink(dir_name, 'cmdb')
reload_cmd = '''service uwsgi stop &&service uwsgi start && systemctl restart celery.service && systemctl reload nginx.service
'''
d = subprocess.call(reload_cmd,shell=True)
print "版本更新完毕"