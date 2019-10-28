#!/usr/bin/env python
# coding:utf-8

from celery import shared_task,current_task

from gitfabu.audit_api import task_distributing_by_group
from api.mysql_api import execute_sqlfile
from audit.models import sql_apply,sql_conf
from gitfabu.models import my_request_task

@shared_task()
def sql_send_message_task(tid,gid):
    task_distributing_by_group(tid,gid)
    return "All Message have been send"

@shared_task()
def sql_execute_task(tid,uid):
    #tid 我的任务id
    #uid sql申请id
    mytask = my_request_task.objects.get(pk=tid)
    sql = sql_apply.objects.get(pk=uid)
    sqlconf = sql.sqlconf
    res = execute_sqlfile(sqlconf.host,sqlconf.port,sqlconf.user,sqlconf.password,sqlconf.workdir,sql.savename)
    sql.islog = True
    log = "开始执行sql：source %s\n"% sql.filename
    if res['out']:
        log = log + "执行结果返回：\n"
        log = log + res['out']
    if res['err']:
        log = log + "执行sql报错：\n"
        log = log + res['err']
    sql.log = log
    sql.save()
    mytask.isend = True
    mytask.status = "已更新"
    mytask.save()
