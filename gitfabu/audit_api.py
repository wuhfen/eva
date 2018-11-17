#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gitfabu.models import my_request_task,git_deploy_audit,git_task_audit,git_deploy,git_code_update
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

def get_the_group_audit_result(my_task_id):
    #输入我的任务,查看所有审核组是否已审核,返回结果列表[true,true,false]
    result = []
    my_task = my_request_task.objects.get(pk=my_task_id)
    groups = list(set([i.audit_group_id for i in my_task.reqt.all() if i]))
    if groups:
        for i in groups:
            if my_task.reqt.filter(audit_group_id=i,isaudit=True):
                result.append(True)
            else:
                result.append(False)
    return result


def change_version_old_to_new(name,platform,classify,method,release,branch=None):
    #提供必要信息,生成新的更新版本
    data = git_deploy.objects.get(name=name,platform=platform,classify=classify,isops=True,islog=True)
    data.islock = True
    data.save()
    old_data = git_code_update.objects.get(code_conf=data,islog=True,isuse=True)
    web_branches = old_data.web_branches
    web_release = old_data.web_release
    php_pc_branches = old_data.php_pc_branches
    php_pc_release = old_data.php_pc_release
    php_mobile_branches = old_data.php_mobile_branches
    php_moblie_release = old_data.php_moblie_release
    js_pc_branches = old_data.js_pc_branches
    js_pc_release = old_data.js_pc_release
    js_mobile_branches = old_data.js_mobile_branches
    js_mobile_release = old_data.js_mobile_release
    config_branches = old_data.config_branches
    config_release = old_data.config_release
    if not branch: branch="master"
    if method == 'web':
        web_release = release[0:7]
        web_branches = branch
    elif method == "php_pc" or method == "php" or method == "vue_php":
        php_pc_release = release[0:7]
        php_pc_branches = branch
    elif method == "php_mobile":
        php_moblie_release = release[0:7]
        php_mobile_branches = branch
    elif method == "js_pc" or method == "js" or method == "vue_pc":
        js_pc_release = release[0:7]
        js_pc_branches = branch
    elif method == "js_mobile" or method == "vue_wap":
        js_mobile_release = release[0:7]
        js_mobile_branches = branch
    else:
        config_branches = branch
        config_release = release[0:7]
    name = "%s-%s-%s-%s-更新"% (platform,classify,name,method)
    updata = git_code_update(name=name,code_conf=data,method=method,version=release[0:7],branch=branch,web_release=web_release,php_pc_release=php_pc_release,
php_moblie_release=php_moblie_release,js_pc_release=js_pc_release,js_mobile_release=js_mobile_release,config_release=config_release,
web_branches=web_branches,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,
js_mobile_branches=js_mobile_branches,config_branches=config_branches,memo=name,details=release,isaudit=True,last_version=data.now_reversion)
    updata.save()
    return updata
