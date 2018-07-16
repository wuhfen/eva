#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from .models import ops_command_log,sql_apply,sql_conf
from gitfabu.models import my_request_task,git_task_audit
from audit.tasks import sql_send_message_task
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse,StreamingHttpResponse
from audit.forms import RecordOPSForm,SqlConfForm
from django.conf import settings
import os,time
import hashlib

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

import pdb
"""sql审计项目"""
def sql_conf_add(request):
    tf = SqlConfForm()
    if request.method == 'POST':
        data = SqlConfForm(request.POST)
        pdb.set_trace()
        if data.is_valid():
            data.save()
    return render(request,'audit/sql_conf_add.html',locals())


def sql_conf_delete(request,uuid):
    data = sql_conf.objects.all()
    sql_data = sql_conf.objects.get(pk=uuid)
    sql_data.delete()
    return render(request,'audit/sql_conf_list.html',locals())


def sql_conf_list(request):
    data = sql_conf.objects.all()
    return render(request,'audit/sql_conf_list.html',locals())

def sql_conf_button(request):
    data = sql_conf.objects.all()
    return render(request,'audit/sql_conf_button.html',locals())

def sql_conf_modify(request,uuid):
    data = sql_conf.objects.all()
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
    errors = []
    if request.method == 'POST':
        database = request.POST.get('database')
        sql_type = request.POST.get('sql_type')
        memo = request.POST.get('memo')
        if not data.group: errors.append("此项目没有配置审核组")
        if not database: errors.append("没有填写数据库名称")
        if sql_type == "file":
            file = request.FILES.get('file')
            md5v = request.POST.get('md5v')
            if not file:errors.append("你没有选择文件")
            if not md5v:errors.append("你没有填写文件的MD5值")
        else:
            statement = request.POST.get('statement')
            md5v = ""
            if not statement:errors.append("你没有填写sql语句")
        if errors: return render(request,'audit/sql_apply_add.html',locals())
        if sql_type == "file":
            basedir = settings.BASE_DIR + "/static/uploads/sql/"
            f_name = file.name + time.strftime("%Y_%m_%d_%H_%M_%S",time.localtime(time.time()))
            filename = os.path.join(basedir,f_name)
            statement = filename
            fobj = open(filename,'wb')
            for chrunk in file.chunks():
                fobj.write(chrunk)
            fobj.close()
        create = sql_apply(name=data,database=database,sql_type=sql_type,md5v=md5v,statement=file.name,file_path="/static/uploads/sql/",file_name=f_name,status="等待审核",memo=memo)
        create.save()
        #发任务
        task_name = "%s申请数据库操作"% data.name
        mytask = my_request_task(name=task_name,table_name="sql_apply",uuid=create.id,initiator=request.user,memo=memo,status="审核中")
        mytask.save()
        sql_send_message_task.delay(mytask.id,data.group.id)
        return JsonResponse({'res':"OK"})
    return render(request,'audit/sql_apply_add.html',locals())

def sql_list(request):
    """列出主机,端口,库名,时间,申请人,状态,等"""
    pass
    return render(request,'audit/sql_list.html',locals())

def sql_file_download(request,filename):
    def file_iterator(file_name,chunk_size=512):
        with open(file_name,"rb+") as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c 
                else:
                    break
    basedir = settings.BASE_DIR + "/static/uploads/sql/"
    filename = os.path.join(basedir,filename)
    res = StreamingHttpResponse(file_iterator(filename))
    res['Content-Type'] = 'application/octet-stream'
    # res['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)
    return res