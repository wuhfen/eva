#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gitfabu.models import my_request_task,git_deploy_audit,git_task_audit
from api.common_api import send_message
from accounts.models import CustomUser,department_Mode

u"""
1、分发审核任务给组内成员
2、检索组内成员审核情况，有一个成员审核该组所有成员标记为已审核
3、单独搞一个一键通过组
"""

def task_distributing_by_group(task_id,group_id):
    group = department_Mode.objects.get(pk=group_id)
    mytask = my_request_task.objects.get(pk=task_id)
    for i in group.members.all():
        task_data = git_task_audit(request_task=mytask,auditor=i,audit_group_id=group.id)
        task_data.save()
        send_message(i,mytask.memo)


def task_distributing(task_id,audit_id):
    audit = git_deploy_audit.objects.get(pk=audit_id)
    mydata = my_request_task.objects.get(pk=task_id)
    for data in audit.group.all():
        for i in data.members.all():
            task_data = git_task_audit(request_task=mydata,auditor=i,audit_group_id=data.id)#保存任务obj，审核人，审核人所属组的id
            task_data.save()
            send_message(i,mydata.memo)


def check_group_audit(task_id,username,status,group_id,postil):
    """只能检测一个组，如果一个用户属于多个组无效，需要改进"""
    mydata = my_request_task.objects.get(pk=task_id)
    if status:
        postil = "《组员%s通过了该任务，本人未操作》"% username
    else:
        postil = "《组员%s否决了该任务，本人未操作》"% username
    try:
        git_task_audit.objects.filter(request_task=mydata,audit_group_id=group_id,isaudit=False).update(isaudit=True,ispass=status,postil=postil)
    except:
        print "未匹配到组%s的任务"% group_id


def onekey_access(task_id,username,status):
    mydata = my_request_task.objects.get(pk=task_id)
    if status:
        text="通过"
        mydata.status = "通过审核，更新中"
    else:
        text="未通过"
        mydata.status = "未通过审核"
        mydata.isend = True
    mydata.save()

    postil = "用户: %s,一键审核：%s"% (username,text)
    data = mydata.reqt.all()
    if data:
        data.update(isaudit=True,ispass=status,postil=postil)
    else:
        print "未匹配到审核任务"


