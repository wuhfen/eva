#!/usr/bin/env python
# coding:utf-8

from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex,MyRunner
from api.common_api import gen_resource
from assets.models import Server

## 引入ansibleAPI，编写调用API的函数
@shared_task()
def do_ansible(task,ip,remark,comment):
    current_task.update_state(state="PROGRESS")
    ansiblex(vars1=task,vars2=ip,vars3=remark,vars4=comment)
    return "12345"

# 后台切换的异步任务，在247上操作nginx.conf文件
@shared_task()
def change_backend_task(host_ip,include_name):
    resource = gen_resource(Server.objects.get(ssh_host=host_ip))
    module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="include vhost/" line="        include vhost/%s.conf;"'% include_name
    print(module_args)
    mytask = MyRunner(resource)
    res = mytask.run('lineinfile',module_args)
    return res

@shared_task()
def change_backend_second(host_ip,include_name,status):
    resource = gen_resource(Server.objects.get(ssh_host=host_ip))
    if status:
        module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="#include vhost/%s.conf" line="        include vhost/%s.conf;"'% (include_name,include_name)
    else:
        module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="include vhost/%s.conf" line="        #include vhost/%s.conf;"'% (include_name,include_name)
    print(module_args)
    shell_args = 'service nginx reload'
    mytask = MyRunner(resource)
    res = mytask.run('lineinfile',module_args)
    res = mytask.run('shell',shell_args)
    return res