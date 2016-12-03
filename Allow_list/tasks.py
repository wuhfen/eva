#!/usr/bin/env python
# coding:utf-8

from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex



## 引入ansibleAPI，编写调用API的函数
@shared_task()
def do_ansible(task,ip,remark,comment):
    current_task.update_state(state="PROGRESS")
    ansiblex(vars1=task,vars2=ip,vars3=remark,vars4=comment)
    return "12345"


# @shared_task()
# def do_ansible(task,ip,remark,comment):
#     task=task
#     ip=ip
#     remark=remark
#     comment=comment

#     current_task.update_state(state="PROGRESS")
#     ansiblex(task,ip,remark,comment)

#     return ip