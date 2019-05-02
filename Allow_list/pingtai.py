#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required


# Create your views here.
from .tasks import nginx_white_copy
from .models import api_access_authorized_conf,api_access_authorized_table
from assets.models import Server
from api.common_api import isValidIp
from api.paginator_api import JuncheePaginator

def strIp_to_listIp(servers):
    servers=servers.strip()
    servers=servers.replace(","," ")
    servers=servers.replace("\r\n"," ")
    servers=servers.replace("\r"," ")
    servers_List=servers.split()
    return servers_List

#------------>白名单服务器配置开始<-------------
def api_white_conf_add(request):
    Errors=[]
    if request.method=='POST':
        name=request.POST.get('name')
        servers=request.POST.get('servers')
        file_path=request.POST.get('file_path')
        default_ip=request.POST.get('default_ip')
        #验证名称是否唯一
        if api_access_authorized_conf.objects.filter(name=name):
            Errors.append("NAME已存在")
            return JsonResponse({'status':"Failed",'info':"NAME已存在!"})
        #验证servers是否存在cmdb中
        servers=strIp_to_listIp(servers)
        for i in servers:
            if not Server.objects.filter(ssh_host=i):
                Errors.append("CMDB中没有%s的信息"% i)
                return JsonResponse({'status':"Failed",'info':"CMDB中没有%s的信息"% i})
        #验证default_ip的有效性
        if default_ip:
            default_ip_list=strIp_to_listIp(default_ip)
            for i in default_ip_list:
                if not isValidIp(i):
                    Errors.append("%s格式错误"% i)
                    return JsonResponse({'status':"Failed",'info':"%s格式错误"% i})
            default_ip=" ".join(default_ip_list)
        data=api_access_authorized_conf(name=name,servers=" ".join(servers),file_path=file_path,default_ip=default_ip)
        data.save()
        return JsonResponse({'status':"OK",'info':"添加成功"})
    return render(request,'allow_list/pingtai_api_white_conf_add.html',locals())

def api_white_conf_list(request):
    data=api_access_authorized_conf.objects.all()
    return render(request,'allow_list/pingtai_api_white_conf_list.html',locals())

def api_white_conf_delete(request,id):
    data=api_access_authorized_conf.objects.get(pk=id)
    data.delete()
    return JsonResponse({'status':"OK",'info':"已删除!"})


def api_white_conf_edit(request,id):
    data=api_access_authorized_conf.objects.get(pk=id)
    if request.method == 'POST':
        name=request.POST.get('name')
        servers=request.POST.get('servers')
        file_path=request.POST.get('file_path')
        default_ip=request.POST.get('default_ip')
        #验证名称是否唯一
        if name != data.name:
            if api_access_authorized_conf.objects.filter(name=name):
                Errors.append("NAME已存在")
                return JsonResponse({'status':"Failed",'info':"NAME已存在!"})
        #验证servers是否存在cmdb中
        servers=strIp_to_listIp(servers)
        for i in servers:
            if not Server.objects.filter(ssh_host=i):
                Errors.append("CMDB中没有%s的信息"% i)
                return JsonResponse({'status':"Failed",'info':"CMDB中没有%s的信息"% i})
        #验证default_ip的有效性
        if default_ip:
            default_ip_list=strIp_to_listIp(default_ip)
            for i in default_ip_list:
                if not isValidIp(i):
                    Errors.append("%s格式错误"% i)
                    return JsonResponse({'status':"Failed",'info':"%s格式错误"% i})
            default_ip=" ".join(default_ip_list)
        data.name=name
        data.servers=" ".join(servers)
        data.file_path=file_path
        data.default_ip=default_ip
        data.save()
        return JsonResponse({'status':"OK",'info':"修改成功"})
    return render(request,'allow_list/pingtai_api_white_conf_edit.html',locals())
#------------>白名单服务器配置结束<-------------


#------------>白名单表操作开始<-------------
def api_white_table_add(request,id):
    conf=api_access_authorized_conf.objects.get(pk=id)
    if request.method=='POST':
        host=request.POST.get('host')
        if not isValidIp(host): return JsonResponse({"status": "Failed","info": "IP格式错误"},safe=False)
        List=[i.host_ip for i in conf.api_access_authorized_table_set.all() if i]
        if conf.api_access_authorized_table_set.filter(host_ip=host): return JsonResponse({"status": "Failed","info": "IP已存在"},safe=False)
        key=request.POST.get('key')
        memo=request.POST.get('memo')
        print memo
        print host
        print key
        api_access_authorized_table.objects.get_or_create(host_key=key,host_ip=host,memo=memo,user=request.user,apiConf=conf)
        return JsonResponse({"status": "OK","info": "已添加"})
    return render(request,'allow_list/pingtai_api_white_table_add.html',locals())

def api_white_table_list(request,id):
    conf=api_access_authorized_conf.objects.get(pk=id)
    data=api_access_authorized_table.objects.filter(apiConf=conf)
    for i in data:
        print i.host_ip
    try:  
        page = int(request.GET.get("page",1))
        if page < 1:  
            page = 1  
    except ValueError:  
        page = 1
    paginator = JuncheePaginator(data, 10)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)
    return render(request,'allow_list/pingtai_api_white_table_list.html',locals())

def api_white_table_delete(request):
    return render(request,'allow_list/pingtai_api_white_table_delete.html',locals())

def api_white_table_edit(request):
    return render(request,'allow_list/pingtai_api_white_table_edit.html',locals())
#------------>白名单表操作结束<-------------