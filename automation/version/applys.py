#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from automation.models import scriptdeploy,scriptlog
from business.models import Business
# Create your views here.
from django.http import JsonResponse
from celery.result import AsyncResult
from automation.tasks import script_update_task

def changes(a,b):
   for i in xrange(0,len(a),b):
       yield  a[i:i+b]

@permission_required('automation.add_scriptdeploy', login_url='/auth_error/')
def version_update(request):
    data = Business.objects.all()
    user = request.user
    taskdata = scriptdeploy.objects.filter(executive_user=user)
    rules = []
    for i in changes(data,5):
        rules.append(i)
    rules0 = rules[0]
    rules1 = rules[1]
    rules2 = rules[2]
    rules3 = rules[3]
    return render(request,'automation/projects_list.html',locals())

@permission_required('automation.add_scriptdeploy', login_url='/auth_error/')
def pull_data(request,choice):
    """用户提交版本发布信息"""
    method = choice
    release = method.split("_")[0]
    enver = method.split("_")[1]

    if "pa" in str(method):
        return render(request,'automation/pull_public.html',locals())
    else:
        print method
        return render(request,'automation/pull_data.html',locals())

@permission_required('automation.add_scriptdeploy', login_url='/auth_error/')
def save_data(request):
    """保存用户提交信息"""
    method = request.GET.get('method')  #存放“1001_new,1001_hd,pa_hd,pa_new”
    memo = request.GET.get('memo')
    sitid = method.split("_")[0]
    release = request.GET.get('release') #存放“a,pp,pa,pam,w,c”
    release_two = request.GET.get('release_two') #存放版本号
    release_three = request.GET.get('release_three')
    user = request.user
    if "hd" in str(method):
        if release == "pa":
            name = "全pc端-public更新"
            method = 'all_hd'
        elif release == "pam":
            name = "全手机端-public更新"
            method = 'all_hd'
        elif release == "pp":
            name = "%s-public更新"% sitid
        elif release == "a":
            name = "%s-完整更新"% sitid
        else:
            name = "%s-web更新"% sitid
        name = "灰度-"+name
    print release_three
    sql_data = scriptdeploy(name=name,sit_id=method,release=release,release_two=release_two,release_three=release_three,memo=memo,executive_user=user)
    sql_data.save()
    data = {'res': "OK",'info': "已经添加到任务列表"}
    return JsonResponse(data)

@permission_required('automation.change_scriptdeploy', login_url='/auth_error/')
def update_online_release(request,uuid):
    """线上更新版本"""
    data = scriptdeploy.objects.get(pk=uuid)
    host = '119.9.91.21'

    if data.sit_id.split("_")[1] == "hd":
        script = "cd /data/shell; ./cmdb-huiduall.sh"
        detype = data.release
        site = data.sit_id.split("_")[0]
        args1 = data.release_two
        args2 = data.release_three
        if detype == 'a':
            command = script + " a " + site + " " + args1 + " " + args2
        elif detype == "pa" or detype == "pam":
            command = script + " " + detype + " " + args1
        else:
            command = script + " " + detype + " " + site + " " + args1
    print command
    obj = script_update_task.delay(uuid,host,command)
    task_id = obj.id
    print task_id
    return render(request,'automation/progress_bar.html',locals())

@permission_required('automation.delete_scriptdeploy', login_url='/auth_error/')
def abolish_release(request,uuid):
    uuid = uuid.split('_')[1]
    scriptdeploy.objects.filter(pk=uuid).update(check_conf=False)
    data = {'res': "OK",'info': "任务已废止！"}
    return JsonResponse(data)

@permission_required('automation.add_scriptdeploy', login_url='/auth_error/')
def update_online_catlog(request,uuid):
    yy = scriptdeploy.objects.get(pk=uuid)
    data = scriptlog.objects.filter(scriptdeploy=yy)
    return render(request,'automation/show_logs.html',locals())