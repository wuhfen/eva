#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from .models import ops_command_log,task_audit
from automation.models import AUser as audit_user
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
import json
import time
from audit.forms import RecordOPSForm,audituserForm
from django.contrib.auth.decorators import login_required, permission_required
from accounts.models import CustomUser
from automation.tasks import gengxin_update_task
# Create your views here.
@permission_required('assets.add_ops_command_log', login_url='/auth_error/')
def record_ops_command(request):
    log_obj = ops_command_log.objects.all()
    return render(request,'audit/record_ops_command.html',locals())

def record_command(request):
    if request.is_ajax():
        start = request.POST['start']
        end = request.POST['end']
        command = request.POST['commd']
        ops_command_log.objects.create(start_time = start,end_time=end,command=command,user=request.user)
        return HttpResponse("success")
    return HttpResponse("error")

@permission_required('assets.add_ops_command_log', login_url='/auth_error/')
def record_command_edit(request,uuid):
    log_obj = ops_command_log.objects.get(pk=uuid)
    rf = RecordOPSForm(instance=log_obj)
    if request.method == 'POST':
        rf = RecordOPSForm(request.POST,instance=log_obj)
        if rf.is_valid():
            rf.save()
    return render(request,'audit/record_command_edit.html',locals())

@login_required()
def my_audit_list(request):
    # data = task_audit.objects.all()
    data = task_audit.objects.filter(auditor=request.user).order_by('-create_date')
    return render(request,'audit/my_audit_list.html',locals())

def my_audit_delete(request,uuid):
    data = task_audit.objects.get(pk=uuid)
    data.delete()
    return HttpResponseRedirect('/audit/my_audit_list/')

def my_audit_modify(request,uuid):
    data = task_audit.objects.get(pk=uuid)
    dict_memo = eval(data.memo)
    common = dict_memo['common']
    env = dict_memo['env']
    method = dict_memo['method']
    if dict_memo.has_key('public_release'):
        pub = dict_memo['public_release']
    else:
        pub = '0'
    if dict_memo.has_key('web_release'):
        web = dict_memo['web_release']
    else:
        web = '0'
    if data.gengxin.code_conf:
        webname = data.gengxin.code_conf.business.name
    siteid = data.gengxin.siteid.replace("m","")
    if env == "test":
        env_name = "测试"
        web_href = "#"
    elif env == "online":
        env_name = "线上"
        web_href = "http://hs"+siteid+".qwas114.com:5"+siteid.replace("f","")
    else:
        web_href = "http://"+siteid+".s1119.com"
        env_name = "灰度"
    if request.method == 'POST':
        ispass = request.POST.get('ispass')
        if ispass == "yes":
            ok = True
        else:
            ok = False
        postil = request.POST.get('postil')
        now = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        data.isaudit = True
        data.ispass = ok 
        data.audit_time = now
        data.postil = postil
        data.save()
        audit_status = eval(data.gengxin.audit_status)
        print "审核前：%s"% audit_status
        for i in audit_status:
            if i['user'] == request.user.username:
                i['ispass'] = ok
                i['isaudit'] = True
                i['postil'] = postil
                i['date'] = now
        if False in [i['isaudit'] for i in audit_status]:
            print "还有用户没有审核"
            data.gengxin.audit_status = audit_status
            data.gengxin.save()
        else:
            if False in [i['ispass'] for i in audit_status]:
                print "审核未通过，任务结束"
                data.gengxin.status = "未通过审核"
            else:
                print "所有审核都通过，开始更新"+siteid
                data.gengxin.status = "更新中"
                meimei = gengxin_update_task.delay(data.gengxin.uuid,env)
            data.gengxin.audit_status = audit_status
            data.gengxin.exist = True
            data.gengxin.execution_time = now
            data.gengxin.save()
        print "审核后：%s"% audit_status
        return JsonResponse({'res':"OK"},safe=False)
    return render(request,'audit/my_audit_modify.html',locals())

def start_audit(request,uuid):
    data = task_audit.objects.get(pk=uuid)
    if request.method == 'POST':
        pass
    return render(request,'audit/start_audit.html',locals())

def audit_user_list(request):
    data = audit_user.objects.all()
    return render(request,'audit/audit_user_list.html',locals())

def audit_user_add(request):
    tf = audituserForm()
    Users = CustomUser.objects.all()
    if request.method == 'POST':
        tf = audituserForm(request.POST)
        if tf.is_valid():
            tf_data = tf.save(commit=False)
            tf_data.save()
            tf.save_m2m()
            return HttpResponseRedirect('/audit/user/list/')
    return render(request,'audit/audit_user_add.html',locals())

def audit_user_delete(request,uuid):
    data = audit_user.objects.get(pk=uuid)
    if data:
        data.delete()
        return HttpResponseRedirect('/audit/user/list/')

def audit_user_modify(request,uuid):
    data = audit_user.objects.get(pk=uuid)
    tf = audituserForm(instance=data)
    Users = CustomUser.objects.all()
    selected_user = data.user.all()
    unselected_users = [p for p in Users if p not in selected_user]
    if request.method == 'POST':
        tf = audituserForm(request.POST, instance=data)
        name = request.POST.get('name')
        print name
        if tf.is_valid():
            tf_data = tf.save(commit=False)
            tf_data.save()
            tf.save_m2m()
            return HttpResponseRedirect('/audit/user/list/')
    return render(request,'audit/audit_user_modify.html',locals())