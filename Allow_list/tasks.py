#!/usr/bin/env python
# coding:utf-8

from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex,MyRunner,MyPlayTask
from api.common_api import gen_resource
from assets.models import Server
from api.ssh_api import ssh_check
## 引入ansibleAPI，编写调用API的函数
@shared_task()
def do_ansible(task,ip,remark,comment):
    current_task.update_state(state="PROGRESS")
    ansiblex(vars1=task,vars2=ip,vars3=remark,vars4=comment)
    return "12345"

@shared_task()
def nginx_white_copy(rss,tfn,fp,wl,isreload,**kw):
    u"""tfn is mean template file name,
    rss is mean remote servers,
    fp is mean file path and file name,
    wl is mean nginx white list,
    isreload is mean nginx service reload
    """
    status = False
    servers = []
    for i in rss.split('\r\n'):
        data = Server.objects.filter(ssh_host=i)
        if len(data) == 0:
            print "CMDB中没有此服务器信息：%s,已跳过！"% i
            continue
        elif len(data) > 1:
            print "CMDB中有多条服务器信息：%s,已跳过！"% i
            continue
        else:
            if not ssh_check(i):
                print "服务器%s不可用，已跳过！"% i
                continue
            else:
                servers.append(Server.objects.get(ssh_host=i))
    if not servers: return "没有可用的服务器，任务结束"

    if isreload: status = True
    playtask = MyPlayTask(gen_resource(servers))
    if "server_name" in kw:
        print "执行蛮牛后台白名单"
        server_name = kw["server_name"]
        siteid = kw["siteid"]
        res = playtask.rsync_nginx_white_conf(tfn,fp,wl,status,server_name,siteid)
    else:
        res = playtask.rsync_nginx_white_conf(tfn,fp,wl,status)
    if res == 0:
        print "结果：成功！"
    elif res == 1:
        print "结果：执行错误！"
    else:
        print "结果：主机不可用！"
    return res

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