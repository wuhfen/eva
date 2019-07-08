#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.
from .models import dsACL_SubProject,dsACL_TopProject,dsACL_ngx,pre_Add_acl,pre_Add_remark
from assets.models import Server
from api.common_api import isValidIp,strIp_to_listIp,utc2beijing,beijing2utc,get_ip_zone
from api.ssh_api import ssh_check,run_ftp
from .tasks import nginx_acl_scp
from datetime import date
from django_celery_beat.models import PeriodicTask,CrontabSchedule,ClockedSchedule
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@login_required()
def pre_add_display(request):
    toppro = dsACL_TopProject.objects.all()
    return render(request,'allow_list/pre_add_display.html',locals())

@login_required()
def pre_add_detail(request):
    pid=request.GET.get('pid')
    preObj = pre_Add_acl.objects.get(pk=pid)
    return render(request,'allow_list/pre_add_detail.html',locals())

@method_decorator(csrf_exempt, name='dispatch')
def pre_add(request):
    res = {'code':0,'msg':"Error request method" ,'count':0}
    status = True
    if request.method == 'POST':
        remark = request.POST.get('remark')
        host = request.POST.get('host')
        server = request.POST.get('server')
        filename = request.POST.get('filename')
        sid = request.POST.get('sid')
        count = request.POST.get('count')
        if not host:return JsonResponse({'code':0,'msg':"Need host"})
        if not server:return JsonResponse({'code':0,'msg':"Need server"})
        if not filename:return JsonResponse({'code':0,'msg':"Need filename"})
        if not remark:return JsonResponse({'code':0,'msg':"Need remark"})
        if not sid:return JsonResponse({'code':0,'msg':"Need sid"})
        if not count: count = 1
        project = dsACL_SubProject.objects.get(pk=sid)
        hosts = [obj.host for obj in dsACL_ngx.objects.filter(project=project)]
        if host in hosts: status = False
        pre, _ = pre_Add_acl.objects.get_or_create(host=host,project=sid,defaults={'status':status})
        data = pre_Add_remark(host=pre,server=server,filename=filename,count=count,remark=remark)
        data.save()
        pre_count=pre.filter_logs.all().count()
        pre.count = pre_count
        pre.save()
        res = {'code':0,'msg':"%s add success"% host,'count':count}
    return JsonResponse(res)

@login_required()
def pre_add_api(request):
    """
    action = "get" 获取数据
    action = "get_today" 获取数据
    action = "effective" 将此IP同步到指定项目（项目无此IP）
    action = "del" 删除
    action = "detail" 详情
    """
    action = request.GET.get("action")
    pid = request.GET.get("id")
    res = {'code':1,'msg':"NO action args",'count':0}
    if action == "get":
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        data=pre_Add_acl.objects.all()[start_line:end_line]
        count = pre_Add_acl.objects.count()
        dataList=[]
        for i in data:
            json_item = eval(i.toJSON(),{'true':1,'false':0,'null':""})
            json_item["ctime"]=utc2beijing(i.ctime)
            json_item["uptime"]=utc2beijing(i.uptime)
            subpro = dsACL_SubProject.objects.get(pk=i.project)
            name = subpro.parentPro.name + subpro.name
            json_item["project"]=name
            dataList.append(json_item)
        res = {'code':0,'msg':"pre-add ip list",'count':count,'data':dataList}
    elif action == 'detail':
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        preObj = pre_Add_acl.objects.get(pk=pid)
        data = preObj.filter_logs.all()[start_line:end_line]
        count = len(data)
        dataList=[]
        for i in data:
            json_item = eval(i.toJSON(),{'true':1,'false':0,'null':""})
            json_item["ctime"]=utc2beijing(i.ctime)
            dataList.append(json_item)
        res = {'code':0,'msg':"pre-add ip list",'count':count,'data':dataList}
    elif action == 'get_today':
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        today = date.today()
        data = pre_Add_acl.objects.filter(uptime__gte=today)[start_line:end_line]
        count = len(data)
        dataList=[]
        for i in data:
            json_item = eval(i.toJSON(),{'true':1,'false':0,'null':""})
            json_item["ctime"]=utc2beijing(i.ctime)
            json_item["uptime"]=utc2beijing(i.uptime)
            subpro = dsACL_SubProject.objects.get(pk=i.project)
            name = subpro.parentPro.name + subpro.name
            json_item["project"]=name
            dataList.append(json_item)
        res={'code':0,'msg':"today pre add list",'count':count,'data':dataList}
    elif action == "del":
        for delId in eval(pid):
            data=pre_Add_acl.objects.get(pk=delId)
            data.delete()
        res={'code':0,'msg':"删除成功",'count':1}
    elif action == "toBlockList":
        for nid in eval(pid):
            data = pre_Add_acl.objects.get(pk=nid)
            remark = ""
            for i in data.filter_logs.all():
                remark += i.remark
            project = dsACL_SubProject.objects.get(pk=data.project)
            a = dsACL_ngx(host=data.host,project=project,user=request.user,remark=remark)
            a.save()
            data.status = False
            data.save()
            res={'code':0,'msg':"转移成功"}
    return JsonResponse(res)

@login_required()
def nginx_acl_display(request):
    topProject = dsACL_TopProject.objects.all()

    return render(request,'allow_list/nginx_acl_display.html',locals())

@login_required()
def nginx_acl_exception(request):
    topProject = dsACL_TopProject.objects.all()
    return render(request,'allow_list/nginx_acl_exception.html',locals())

@login_required()
def nginx_acl_add(request):
    if request.method == 'POST':
        host=request.POST.get('host')
        host_list = strIp_to_listIp(host)
        for ip in host_list:
            if not isValidIp(ip): return JsonResponse({'code':1,'msg':'IP格式错误!','count':0})
        tid = request.POST.get('topproject')
        top_obj = dsACL_TopProject.objects.get(pk=tid)
        sid = request.POST.get('project')
        sub_obj = dsACL_SubProject.objects.get(pk=sid)
        deltask = request.POST.get('delTask')
        delDateTime = request.POST.get('delDateTime')
        delDateTime = beijing2utc(delDateTime)
        remark = request.POST.get('remark')
        # 判断添加限制,特权IP
        limit = top_obj.limit
        exception = top_obj.exception
        if limit != 0:
            subps=dsACL_SubProject.objects.filter(parentPro=top_obj)
            for ip in host_list:
                ipNum = 0
                for subpro in subps:
                    ipNum += dsACL_ngx.objects.filter(project=subpro,host=ip).count()
                if ipNum >= limit and ip not in exception:
                    return JsonResponse({'code':1,'msg':'IP: %s 添加次数大于 %s'% (ip,limit),'count':0})
        if not deltask:
            deltask = False
            delDateTime = None
        else:
            deltask = True
        for ipaddr in host_list:
            if dsACL_ngx.objects.filter(project=sub_obj,host=ipaddr):return JsonResponse({'code':1,'msg':'IP: %s 已存在 %s'% (ip,sub_obj.name),'count':0})
            data = dsACL_ngx(host=ipaddr,zone=get_ip_zone(ipaddr),project=sub_obj,user=request.user,remark=remark,delTask=deltask,delDateTime=delDateTime)
            data.save()
            if deltask:
                schedule, _ = ClockedSchedule.objects.get_or_create(
                    clocked_time = data.delDateTime
                )
                PeriodicTask.objects.create(
                    name = "acl_delIp_%s"% data.host
                    ,task = "Allow_list.tasks.nginx_acl_del"
                    ,clocked = schedule
                    ,args = json.dumps([data.id])
                    ,one_off = True
                    ,enabled = True
                )
        # 调用异步任务同步文件
        nginx_acl_scp.delay(sid)
        return JsonResponse({'code':0,'msg':'IP添加完成'})
    return render(request,'allow_list/nginx_acl_add.html',locals())



def nginx_acl_api(request):
    sid = request.GET.get('sid')
    hid = request.GET.get('id')
    action = request.GET.get('action')
    value = request.GET.get('value')
    if action == "get":
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        keyword = request.GET.get('keyword')
        if keyword:
            if sid:
                subpro = dsACL_SubProject.objects.get(pk=sid)
                data = dsACL_ngx.objects.filter(project=subpro,host__contains=keyword)[start_line:end_line]
                count = dsACL_ngx.objects.filter(project=subpro,host__contains=keyword).count()
            else:
                tid = request.GET.get('tid')
                if tid:
                    toppro = dsACL_TopProject.objects.get(pk=tid)
                    subpro_list = dsACL_SubProject.objects.filter(parentPro=toppro)
                    data = []
                    for subpro in subpro_list:
                        for host in dsACL_ngx.objects.filter(project=subpro):
                            if keyword in host.host: data.append(host)
                    count = len(data)
                    data = data[start_line:end_line]
                else:
                    data = dsACL_ngx.objects.filter(host__contains=keyword)[start_line:end_line]
                    count = dsACL_ngx.objects.filter(host__contains=keyword).count()
        else:
            if sid:
                subpro = dsACL_SubProject.objects.get(pk=sid)
                data = dsACL_ngx.objects.filter(project=subpro)[start_line:end_line]
                count = dsACL_ngx.objects.filter(project=subpro).count()
            else:
                data = dsACL_ngx.objects.all()[start_line:end_line]
                count = dsACL_ngx.objects.count()
        dataList=[]
        for i in data:
            json_item = eval(i.toJSON(),{'true':1,'false':0,'null':""})
            json_item["user"]=i.user.username
            json_item["ctime"]=utc2beijing(i.ctime)
            json_item["delDateTime"]=utc2beijing(i.delDateTime)
            dataList.append(json_item)
        res={'code':0,'msg':"",'count':count,'data':dataList}
    elif action == 'get_today':
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        today = date.today()
        data = dsACL_ngx.objects.filter(ctime__gte=today)[start_line:end_line]
        count = len(data)
        dataList=[]
        for i in data:
            json_item = eval(i.toJSON(),{'true':1,'false':0,'null':""})
            json_item["user"]=i.user.username
            json_item["ctime"]=utc2beijing(i.ctime)
            json_item["delDateTime"]=utc2beijing(i.delDateTime)
            dataList.append(json_item)
        res={'code':0,'msg':"",'count':count,'data':dataList}
    elif action == "change_remark":
        data = dsACL_ngx.objects.get(pk=hid)
        data.remark = value
        data.save()
        res={'code':0,'msg':"备注已修改",'count':1}
    elif action == "change_delDateTime":
        data = dsACL_ngx.objects.get(pk=hid)
        data.delDateTime = beijing2utc(value)
        data.save()
        if data.delTask:
            name = "acl_delIp_%s"% data.host
            task = PeriodicTask.objects.get(
                name=name
                ,task = "Allow_list.tasks.nginx_acl_del"
                ,args = json.dumps([data.id])
            )
            schedule, _ = ClockedSchedule.objects.get_or_create(
                clocked_time = data.delDateTime
            )
            task.clocked = schedule
            task.save()
        res={'code':0,'msg':"删除时间已设定",'count':1}
    elif action == "change_task":
        data = dsACL_ngx.objects.get(pk=hid)
        if value == 'True':
            if not data.delDateTime: return JsonResponse({'code':1,'msg':"你还没有设定删除时间",'count':1})
            value = True
            schedule, _ = ClockedSchedule.objects.get_or_create(
                clocked_time = data.delDateTime
            )
            if not _:
                schedule.enabled = True
                schedule.save()
            task, _ = PeriodicTask.objects.get_or_create(
                name = "acl_delIp_%s"% data.host
                ,task = "Allow_list.tasks.nginx_acl_del"
                ,args = json.dumps([data.id])
                ,defaults={'clocked':schedule,"one_off":True,"enabled":True}
            )
            if not _:
                task.clocked = schedule
                task.one_off = True
                task.enabled = True
                task.save()
        else:
            value = False
            task = PeriodicTask.objects.get(
                name = "acl_delIp_%s"% data.host
                ,task = "Allow_list.tasks.nginx_acl_del"
                ,args = json.dumps([data.id])
            )
            if task:
                task.enabled = False
                task.save()
        data.delTask = value
        data.save()
        res={'code':0,'msg':"修改定时任务",'count':1}
    elif action == "del":
        for delID in eval(hid):
            data = dsACL_ngx.objects.get(pk=delID)
            sid = data.project.id
            if data.delTask:
                name = "acl_delIp_%s"% data.host
                task = PeriodicTask.objects.get(
                    name=name
                    ,task = "Allow_list.tasks.nginx_acl_del"
                    ,args = json.dumps([data.id])
                )
                if task: task.delete()
            data.delete()
            nginx_acl_scp.delay(sid)
        res={'code':0,'msg':"删除成功",'count':1}

    return JsonResponse(res)

@login_required()
def top_pro_display(request):
    return render(request,'allow_list/top_pro_display.html')

@login_required()
def top_pro_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        hosts = request.POST.get('servers')
        filename = request.POST.get('filename')
        rule = request.POST.get('rule')
        limit = request.POST.get('limit')
        exception = request.POST.get('exception')
        globalip = request.POST.get('globalip')
        hook = request.POST.get('hook')
        remark = request.POST.get('remark')
        if dsACL_TopProject.objects.filter(name=name): return JsonResponse({'code':1,'msg':"该项目已存在",'count':1})
        if hosts:
            for i in strIp_to_listIp(hosts):
                if not isValidIp(i): return JsonResponse({'code':1,'msg':"目标服务器IP格式错误",'count':1})
        if exception:
            for i in strIp_to_listIp(exception):
                if not isValidIp(i): return JsonResponse({'code':1,'msg':"无限制IP格式错误",'count':1})
        if globalip:
            for i in strIp_to_listIp(globalip):
                if not isValidIp(i): return JsonResponse({'code':1,'msg':"默认添加IP格式错误",'count':1})
        if not limit: limit=0
        data=dsACL_TopProject(name=name,servers=hosts,filename=filename,rule=rule,limit=limit,exception=exception,globalip=globalip,hook=hook,remark=remark)
        data.save()
        return JsonResponse({'code':0,'msg':"添加成功",'count':1})
    return render(request,'allow_list/top_pro_add.html',locals())


@login_required()
def top_servers_edit(request):
    tid=request.GET.get('tid')
    print "检查项目%s 的目标服务器可用性"% tid
    return render(request,'allow_list/top_pro_edit_server.html',locals())

@login_required()
def top_exception_edit(request):
    tid=request.GET.get('tid')
    return render(request,'allow_list/top_pro_edit_exception.html',locals())

@login_required()
def top_global_edit(request):
    tid=request.GET.get('tid')
    return render(request,'allow_list/top_pro_edit_globalip.html',locals())

@login_required()
def top_pro_api(request):
    """
    id: id
    action: get 获取字段 value为搜索条件keyword,另外有limit和page参数
    action: del 删除
    action: edit_name 编辑名字
    action: edit_servers 编辑服务器信息
    action: check_servers 检测服务器状态
    action: add_servers 添加
    action: del_servers 删除目标服务器
    action: edit_filename 编辑文件路径信息
    action: edit_rule 编辑匹配规则
    action: edit_limit 编辑限制条目
    action: edit_exception 编辑特权IP
    action: get_exception 获取特权ip
    action: add_exception 添加特权ip
    action: del_exception 删除特权ip
    action: edit_global 编辑默认IP
    action: get_global 获取默认ip
    action: add_global 添加默认ip
    action: del_global 删除默认ip
    action: edit_hook 编辑钩子
    action: edit_remark 编辑备注
    value: 对应值
    """
    action = request.GET.get('action')
    tid = request.GET.get('id')
    value = request.GET.get('value')
    if action == "get":
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        keyword = request.GET.get('keyword')
        if keyword:
            data = dsACL_TopProject.objects.filter(name__contains=keyword)[start_line:end_line]
            count = len(data)
        else:
            data = dsACL_TopProject.objects.all()[start_line:end_line]
            count = dsACL_TopProject.objects.count()
        res={'code':0,'msg':"",'count':count,'data':[eval(i.toJSON()) for i in data if i]}
    elif action == "getAll":
        data = dsACL_TopProject.objects.all()
        res={'code':0,'msg':"所有top项目",'count':len(data),'data':[eval(i.toJSON()) for i in data if i]}
    elif action == "edit_name":
        if dsACL_TopProject.objects.filter(name=value): return JsonResponse({'code':1,'msg':"该项目已存在",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        data.name=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_filename":
        data = dsACL_TopProject.objects.get(pk=tid)
        data.filename=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_rule":
        data = dsACL_TopProject.objects.get(pk=tid)
        data.rule=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_limit":
        if not value:value = 0
        data = dsACL_TopProject.objects.get(pk=tid)
        data.limit=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_hook":
        data = dsACL_TopProject.objects.get(pk=tid)
        data.hook=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_remark":
        data = dsACL_TopProject.objects.get(pk=tid)
        data.remark=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_servers":
        value=value.split('@')
        before_host=value[0]
        after_host=value[1]
        if not isValidIp(after_host): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        servers = "\n".join([after_host if x == before_host else x for x in strIp_to_listIp(data.servers)])
        data.servers = servers
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_exception":
        value=value.split('@')
        before_host=value[0]
        after_host=value[1]
        if not isValidIp(after_host): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        exception = "\n".join([after_host if x == before_host else x for x in strIp_to_listIp(data.exception)])
        data.exception = exception
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "del":
        for delID in eval(tid):
            data = dsACL_TopProject.objects.get(pk=delID)
            data.delete()
        res={'code':0,'msg':"删除成功",'count':1}
    elif action == "check_servers":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = data.servers
        server_List=[]
        servers=[]
        if hosts:
            servers = strIp_to_listIp(hosts)
            for i in servers:
                if Server.objects.filter(ssh_host=i):
                    server_List.append({"host":i,"isexists":True,"status":ssh_check(i)})
                else:
                    server_List.append({"host":i,"isexists":False,"status":False})
        res = {'code':0,'msg':"目标服务器检测",'count':len(servers),'data':server_List}
    elif action == "add_servers":
        if not isValidIp(value): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts=[]
        if data.servers: hosts = strIp_to_listIp(data.servers)
        if value in hosts: return JsonResponse({'code':1,'msg':"此IP已存在",'count':1})
        hosts.append(value)
        servers = "\n".join(hosts)
        data.servers = servers
        data.save()
        res={'code':0,'msg':"添加目标服务器成功",'count':1}
    elif action == "del_servers":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = strIp_to_listIp(data.servers)
        hosts = [x for x in hosts if x!=value]
        if hosts:
            servers = "\n".join(hosts)
        else:
            servers = ""
        data.servers = servers
        data.save()
        res={'code':0,'msg':"删除目标服务器成功",'count':1}
    elif action == "get_exception":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = data.exception
        server_List=[]
        servers=[]
        if hosts:
            servers = strIp_to_listIp(hosts)
            for i in servers:
                server_List.append({"host":i})
        res = {'code':0,'msg':"特权IP查看",'count':len(servers),'data':server_List}
    elif action == "add_exception":
        if not isValidIp(value): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts=[]
        if data.exception: hosts = strIp_to_listIp(data.exception)
        if value in hosts: return JsonResponse({'code':1,'msg':"此IP已存在",'count':1})
        hosts.append(value)
        exception = "\n".join(hosts)
        data.exception = exception
        data.save()
        res={'code':0,'msg':"添加特权IP成功",'count':1}
    elif action == "del_exception":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = strIp_to_listIp(data.exception)
        hosts = [x for x in hosts if x!=value]
        if hosts:
            exception = "\n".join(hosts)
        else:
            exception = ""
        data.exception = exception
        data.save()
        res={'code':0,'msg':"删除特权IP成功",'count':1}
    elif action == "get_global":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = data.globalip
        server_List=[]
        servers=[]
        if hosts:
            servers = strIp_to_listIp(hosts)
            for i in servers:
                server_List.append({"host":i})
        res = {'code':0,'msg':"默认IP查看",'count':len(servers),'data':server_List}
    elif action == "add_global":
        if not isValidIp(value): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts=[]
        if data.globalip: hosts = strIp_to_listIp(data.globalip)
        if value in hosts: return JsonResponse({'code':1,'msg':"此IP已存在",'count':1})
        hosts.append(value)
        globalip = "\n".join(hosts)
        data.globalip = globalip
        data.save()
        res={'code':0,'msg':"添加全局默认IP成功",'count':1}
    elif action == "del_global":
        data = dsACL_TopProject.objects.get(pk=tid)
        hosts = strIp_to_listIp(data.globalip)
        hosts = [x for x in hosts if x!=value]
        if hosts:
            globalip = "\n".join(hosts)
        else:
            globalip = ""
        data.globalip = globalip
        data.save()
        res={'code':0,'msg':"删除默认IP成功",'count':1}
    elif action == "edit_global":
        value=value.split('@')
        before_host=value[0]
        after_host=value[1]
        if not isValidIp(after_host): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_TopProject.objects.get(pk=tid)
        globalip = "\n".join([after_host if x == before_host else x for x in strIp_to_listIp(data.globalip)])
        data.globalip = globalip
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    return JsonResponse(res)

@login_required()
def sub_pro_display(request):
    tid=request.GET.get('tid')
    toppro=dsACL_TopProject.objects.get(pk=tid)
    topname=toppro.name

    return render(request,'allow_list/sub_pro_display.html',locals())

@login_required()
def sub_pro_add(request,tid):
    toppro=dsACL_TopProject.objects.get(pk=tid)
    if request.method == "POST":
        name = request.POST.get('name')
        useParentConf = request.POST.get('useParentConf')
        if useParentConf: 
            useParentConf=False
        else:
            useParentConf=True
        hosts = request.POST.get('servers')
        filename = request.POST.get('filename')
        rule = request.POST.get('rule')
        hook = request.POST.get('hook')
        remark = request.POST.get('remark')
        if dsACL_SubProject.objects.filter(parentPro=toppro,name=name): return JsonResponse({'code':1,'msg':"该项目已存在",'count':1})
        if hosts:
            for i in strIp_to_listIp(hosts):
                if not isValidIp(i): return JsonResponse({'code':1,'msg':"目标服务器IP格式错误",'count':1})

        data=dsACL_SubProject(name=name,parentPro=toppro,useParentConf=useParentConf,servers=hosts,filename=filename,rule=rule,hook=hook,remark=remark)
        data.save()
        return JsonResponse({'code':0,'msg':"子项目添加成功",'count':1})
    return render(request,'allow_list/sub_pro_add.html',locals())

@login_required()
def sub_pro_api(request):
    action = request.GET.get('action')
    sid = request.GET.get('id')
    tid = request.GET.get('tid')
    toppro = dsACL_TopProject.objects.get(pk=tid)
    value = request.GET.get('value')
    res={'code':1,'msg':"错误",'count':0}
    if action == "get":
        page = request.GET.get('page')
        limit = request.GET.get('limit')
        if page==1:
            start_line=0
            end_line=limit
        else:
            start_line=int(page)*int(limit)-int(limit)
            end_line=int(page)*int(limit)
        keyword = request.GET.get('keyword')
        if keyword:
            data = dsACL_SubProject.objects.filter(parentPro=toppro,name__contains=keyword)
        else:
            data = dsACL_SubProject.objects.filter(parentPro=toppro)
        count = len(data)
        data = data[start_line:end_line]
        res={'code':0,'msg':"",'count':count,'data':[eval(i.toJSON(),{'true':1,'false':0}) for i in data if i]}
    elif action == "getAll":
        data = dsACL_SubProject.objects.filter(parentPro=toppro)
        res={'code':0,'msg':"所有sub项目",'count':len(data),'data':[eval(i.toJSON(),{'true':1,'false':0}) for i in data if i]}
    elif action == "edit_name":
        if dsACL_SubProject.objects.filter(parentPro=toppro,name=value): return JsonResponse({'code':1,'msg':"项目名已存在",'count':1})
        data = dsACL_SubProject.objects.get(pk=sid)
        data.name=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_filename":
        data = dsACL_SubProject.objects.get(pk=sid)
        data.filename=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_rule":
        data = dsACL_SubProject.objects.get(pk=sid)
        data.rule=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == 'edit_hook':
        data = dsACL_SubProject.objects.get(pk=sid)
        data.hook=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == 'edit_remark':
        data = dsACL_SubProject.objects.get(pk=sid)
        data.remark=value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "del":
        for delID in eval(sid):
            data = dsACL_SubProject.objects.get(pk=delID)
            data.delete()
        res={'code':0,'msg':"删除sub项目成功",'count':1}
    elif action == "check_servers":
        data = dsACL_SubProject.objects.get(pk=sid)
        hosts = data.servers
        server_List=[]
        servers=[]
        if hosts:
            servers = strIp_to_listIp(hosts)
            for i in servers:
                if Server.objects.filter(ssh_host=i):
                    server_List.append({"host":i,"isexists":True,"status":ssh_check(i)})
                else:
                    server_List.append({"host":i,"isexists":False,"status":False})
        res = {'code':0,'msg':"目标服务器检测",'count':len(servers),'data':server_List}
    elif action == "add_servers":
        if not isValidIp(value): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_SubProject.objects.get(pk=sid)
        hosts=[]
        if data.servers: hosts = strIp_to_listIp(data.servers)
        if value in hosts: return JsonResponse({'code':1,'msg':"此IP已存在",'count':1})
        hosts.append(value)
        servers = "\n".join(hosts)
        data.servers = servers
        data.save()
        res={'code':0,'msg':"添加目标服务器成功",'count':1}
    elif action == "del_servers":
        data = dsACL_SubProject.objects.get(pk=sid)
        hosts = strIp_to_listIp(data.servers)
        hosts = [x for x in hosts if x!=value]
        if hosts:
            servers = "\n".join(hosts)
        else:
            servers = ""
        data.servers = servers
        data.save()
        res={'code':0,'msg':"删除目标服务器成功",'count':1}
    elif action == "edit_servers":
        value=value.split('@')
        before_host=value[0]
        after_host=value[1]
        if not isValidIp(after_host): return JsonResponse({'code':1,'msg':"IP格式错误",'count':1})
        data = dsACL_SubProject.objects.get(pk=sid)
        servers = "\n".join([after_host if x == before_host else x for x in strIp_to_listIp(data.servers)])
        data.servers = servers
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    elif action == "edit_useParentConf":
        data = dsACL_SubProject.objects.get(pk=sid)
        if value=="True":
            value=True
            print "使用top配置"
        else:
            value=False
            print "使用sub配置"
        data.useParentConf = value
        data.save()
        res={'code':0,'msg':"修改成功",'count':1}
    return JsonResponse(res)

@login_required()
def sub_servers_edit(request):
    tid=request.GET.get('tid')
    sid=request.GET.get('sid')
    print "检查项目%s 的目标服务器可用性"% sid
    return render(request,'allow_list/sub_pro_edit_server.html',locals())
