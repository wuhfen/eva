#!/usr/bin/env python
# coding:utf-8

from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from api.ansible_api import ansiblex, MyRunner, MyPlayTask
from api.common_api import gen_resource,isValidIp,strIp_to_listIp
from assets.models import Server
from .models import dsACL_TopProject,dsACL_SubProject,dsACL_ngx
from api.ssh_api import ssh_check,run_ftp,run_cmd
# 引入ansibleAPI，编写调用API的函数

#shared_task 装饰器，使写在app内的任务可以被celery实时调度
#current_task 方法，可以更改任务的状态，自定义状态

import time
@shared_task()
def test_django_beat(args):
    now = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print "打印：%s 时间：%s"% (args,now)




@shared_task()
def do_ansible(task, ip, remark, comment):
    current_task.update_state(state="PROGRESS")
    ansiblex(vars1=task, vars2=ip, vars3=remark, vars4=comment)
    return "12345"


@shared_task()
def nginx_white_copy(rss, tfn, fp, wl, isreload, **kw):
    """tfn is mean template file name,
    rss is mean remote servers,
    fp is mean file path and file name,
    wl is mean nginx white list,
    isreload is mean nginx service reload
    """
    status = False
    servers = []
    for i in rss.split('\r\n'):
        print i
        data = Server.objects.filter(ssh_host=i)
        if len(data) == 0:
            print "CMDB中没有此服务器信息：%s,已跳过！" % i
            continue
        elif len(data) > 1:
            print "CMDB中有多条服务器信息：%s,已跳过！" % i
            continue
        else:
            if not ssh_check(i):
                print "服务器%s不可用，已跳过！" % i
                continue
            else:
                servers.append(Server.objects.get(ssh_host=i))
    if not servers:
        return "没有可用的服务器，任务结束"

    if isreload:
        status = True
    playtask = MyPlayTask(gen_resource(servers))
    if "server_name" in kw:
        print "执行蛮牛后台白名单"
        server_name = kw["server_name"]
        siteid = kw["siteid"]
        res = playtask.rsync_nginx_white_conf(tfn, fp, wl, status, server_name, siteid)
    else:
        res = playtask.rsync_nginx_white_conf(tfn, fp, wl, status)
    if res == 0:
        print "结果：成功！"
    elif res == 1:
        print "结果：执行错误！"
    else:
        print "结果：主机不可用！"
    return res


@shared_task()
def change_backend_task(host_ip, include_name):
    # 后台切换的异步任务，在247上操作nginx.conf文件
    resource = gen_resource(Server.objects.get(ssh_host=host_ip))
    module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="include vhost/" line="        include vhost/%s.conf;"' % include_name
    print(module_args)
    mytask = MyRunner(resource)
    res = mytask.run('lineinfile', module_args)
    return res


@shared_task()
def change_backend_second(host_ip, include_name, status):
    resource = gen_resource(Server.objects.get(ssh_host=host_ip))
    if status:
        module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="#include vhost/%s.conf" line="        include vhost/%s.conf;"' % (include_name, include_name)
    else:
        module_args = 'dest="/usr/local/nginx/conf/nginx.conf" regexp="include vhost/%s.conf" line="        #include vhost/%s.conf;"' % (include_name, include_name)
    print(module_args)
    shell_args = 'service nginx reload'
    mytask = MyRunner(resource)
    res = mytask.run('lineinfile', module_args)
    res = mytask.run('shell', shell_args)
    return res


def nginx_acl_task(sid):
    """CMDB访问控制系统将本地文件上传到服务器"""
    sub_obj = dsACL_SubProject.objects.get(pk=sid)
    top_obj = sub_obj.parentPro
    if sub_obj.useParentConf:
        servers = top_obj.servers
        filename = top_obj.filename
        rule = top_obj.rule
        hook = top_obj.hook
    else:
        servers = sub_obj.servers
        filename = sub_obj.filename
        rule = sub_obj.rule
        hook = sub_obj.hook
    # 推送文件
    ruleIp = ""
    for acl_obj in dsACL_ngx.objects.filter(project=sub_obj):
        ruleIp = ruleIp + rule.replace("{IP}", acl_obj.host) + '\n'
    localfile = "/data/nginx_acl_cmdb/aclTmpfile"
    with open(localfile, "wb+") as f:
        f.write(ruleIp)
    for server in strIp_to_listIp(servers):
        try:
            server_obj = Server.objects.get(ssh_host=server)
        except:
            server_obj = Server.objects.filter(ssh_host=server)[0]
        run_ftp(server, int(server_obj.ssh_port), server_obj.ssh_password, server_obj.ssh_user, localfile, filename)
        if hook:
            res = run_cmd(server, int(server_obj.ssh_port), server_obj.ssh_password, server_obj.ssh_user,hook)


@shared_task()
def nginx_acl_scp(sid):
    nginx_acl_task(sid)
    return "nginx aclfile task end"

@shared_task()
def nginx_acl_del(nid):
    ip = dsACL_ngx.objects.get(pk=nid)
    subpro = ip.project
    ip.delete()
    nginx_acl_task(subpro.id)
    return "nginx acl del task end"

def cashSourceLogFilter(sid):
    """现金网源站日志过滤,使用ansible api或者使用python paramiko模块
    ansible驱动脚本
    脚本 input 1.匹配规则 2.sid 3.IPaddr
         output 请求papi接口，传送所需参数
    paramiko 调用资产组内的host
    
    """
    





@shared_task()
def BlockIpPreAdd(sid):
    """定时任务，每日从日志文件里过滤出可疑IP，发送到预添加数据库里
    根据sub Project id来调用不同平台的过滤方法，避免强耦合
    """
    pass
    return "BlockIpPreAdd Task END"


