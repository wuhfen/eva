#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from .models import ops_command_log,sql_apply,sql_conf,sql_DangousKey
from accounts.models import department_Mode as Groups
from gitfabu.models import my_request_task,git_task_audit
from audit.tasks import sql_send_message_task
from django.http import HttpResponse, JsonResponse,StreamingHttpResponse
from audit.forms import RecordOPSForm,SqlConfForm
from django.conf import settings
import os,time
import hashlib
from api.mysql_api import mysql_alive

# Create your views here.
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

def record_command_edit(request,uuid):
    log_obj = ops_command_log.objects.get(pk=uuid)
    rf = RecordOPSForm(instance=log_obj)
    if request.method == 'POST':
        rf = RecordOPSForm(request.POST,instance=log_obj)
        if rf.is_valid():
            rf.save()
    return render(request,'audit/record_command_edit.html',locals())


"""sql审计项目"""
def sql_conf_add(request):
    """创建目录，测试mysql的状态"""
    tf = SqlConfForm()
    if request.method == 'POST':
        name = request.POST.get('name')
        host = request.POST.get('host')
        user = request.POST.get('user')
        port = request.POST.get('port')
        password = request.POST.get('password')
        apply_group = request.POST.get('apply_group')
        apply_group = Groups.objects.get(pk=apply_group)
        group = request.POST.get('group')
        group = Groups.objects.get(pk=group)
        group_ops = request.POST.get('group_ops')
        group_ops = Groups.objects.get(pk=group_ops)
        workdir = "/data/sqlfile/%s_%s"% (host,port)
        status = mysql_alive(host,password,user=user,port=port)

        data = sql_conf(name=name,host=host,port=port,user=user,password=password,apply_group=apply_group,group=group,group_ops=group_ops,workdir=workdir,status=status)
        data.save()
        if not os.path.exists(workdir):os.makedirs(workdir)
    return render(request,'audit/sql_conf_add.html',locals())


def sql_conf_check_status(request,uuid):
    data = sql_conf.objects.get(pk=uuid)
    status = mysql_alive(data.host,data.password,user=data.user,port=data.port)
    if status:
        res = {"code":0,"msg":"online"}
    else:
        res = {"code":1,"msg":"offline"}
    data.status = status
    data.save()
    return JsonResponse(res)

def sql_conf_delete(request,uuid):
    sql_data = sql_conf.objects.get(pk=uuid)
    sql_data.delete()
    return render(request,'audit/sql_conf_list.html',locals())


def sql_conf_list(request):
    data = sql_conf.objects.all()
    return render(request,'audit/sql_conf_list.html',locals())

def sql_conf_button(request):
    data = []
    user = request.user

    for g in user.group_users.all():
        conf = sql_conf.objects.filter(apply_group=g)
        if conf: data+=conf
    return render(request,'audit/sql_conf_button.html',locals())

def sql_conf_modify(request,uuid):
    sql_data = sql_conf.objects.get(pk=uuid)
    tf = SqlConfForm(instance=sql_data)
    if request.method == "POST":
        tf = SqlConfForm(request.POST,instance=sql_data)
        if tf.is_valid():
            tf.save()
            return JsonResponse({'res':"OK"})
    return render(request,'audit/sql_conf_modify.html',locals())

def md5sum(file):
    """返回文件的md5值"""
    fd = open(file,"r")
    fr = fd.read()
    fd.close()
    md5 = hashlib.md5(fr)
    return md5.hexdigest()


def sql_apply_add(request,uuid):
    data = sql_conf.objects.get(pk=uuid)
    if request.method == 'POST':
        user = request.user
        if data.apply_group:
            apply_group_members = data.apply_group.members.all()
            if user not in apply_group_members:
                return JsonResponse({'code':1,'msg':"你没有权限!"})
        else:
            return JsonResponse({'code':1,'msg':"项目缺少申请权限组!"})
        memo = request.POST.get('memo')
        file = request.FILES.get('file')
        md5v = request.POST.get('md5v')
        if not file:return JsonResponse({'code':1,'msg':"沒有文件"})
        if ".sql" not in file.name: return JsonResponse({'code':1,'msg':"文件应该已.sql结尾"})
        if not md5v:return JsonResponse({'code':1,'msg':"沒有提供文件MD5值"})


        basedir = data.workdir
        savename = file.name + "_" + time.strftime("%Y_%m_%d_%H_%M_%S",time.localtime(time.time()))
        filename = os.path.join(basedir,savename)
        with open(filename,'wb') as f:
            for chrunk in file.chunks():
                f.write(chrunk)
        dangerous = False
        keyword = []
        dangerous_key_list =[key.dkey for key in sql_DangousKey.objects.all() if key]
        if dangerous_key_list:
            with open(filename,"r+") as f:
                f_list = f.readlines()
            for key in dangerous_key_list:
                for sentence in f_list:
                    if key in sentence.lower():
                        dangerous = True
                        keyword.append(sentence.rstrip('\n'))
        if keyword:
            keyword = " ".join(keyword)
        else:
            keyword = ""
        md5save = md5sum(filename)
        if md5v == md5save:
            create = sql_apply(sqlconf=data,filename=file.name,savename=savename,dangerous=dangerous,keyword=keyword,md5value=md5save,md5user=md5v,memo=memo,user=request.user)
            create.save()
        else:
            os.remove(filename)
            return JsonResponse({'code':1,'msg':"提供的MD5值与文件不匹配"})

        #发任务,关键字发任务,如果sql文件里过滤出del,drop等有关键字,则需要多加一个运维组审核
        task_name = "%s申请数据库操作"% data.name
        mytask = my_request_task(name=task_name,types="mysql",table_name="sql_apply",uuid=create.id,initiator=request.user,memo=memo,status="审核中")
        mytask.save()
        sql_send_message_task.delay(mytask.id,data.group.id)
        if dangerous:
            sql_send_message_task.delay(mytask.id,data.group_ops.id)
        return JsonResponse({'code':0,'msg':"sql任务创建成功"})
    if not data.status:return HttpResponse("当前配置连不上数据库！")
    return render(request,'audit/sql_apply_add.html',locals())

def sql_list(request):
    """列出主机,端口,库名,时间,申请人,状态,等"""
    pass
    return render(request,'audit/sql_list.html',locals())

def sql_file_download(request,uuid):
    def file_iterator(file_name,chunk_size=512):
        with open(file_name,"rb+") as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c 
                else:
                    break
    data = sql_apply.objects.get(pk=uuid)
    filename = os.path.join(data.sqlconf.workdir,data.savename)
    print filename
    res = StreamingHttpResponse(file_iterator(filename))
    res['Content-Type'] = 'application/octet-stream'
    # res['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)
    return res