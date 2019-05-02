#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from assets.models import Service, Project, sqlpasswd
from assets.models import Asset, Server, NIC, RaidAdaptor, Disk, CPU, RAM
from forms import ServerForm, AssetForm, CPUForm, RAMForm, DiskForm, NICForm, RaidForm, SQLpassForm
# Create your views here.
from ansible_update_assert import asset_ansible_update
import re
import time, hmac, hashlib, json
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from api.paginator_api import JuncheePaginator


def isValidIp(ip):  
    if re.match(r"^\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$", ip): return True
    return False  
      
def isValidMac(mac):  
    if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac): return True
    return False 

##还没有对网卡输入的IP与mac进行验证，上面定义两个函数，有时间在进行处理，最好使用前端js进行验证，不用后端处理


def get_auth_obj(request):
    user = request.user.username
    gateone_server = 'https://47.89.28.88:10443'
    secret ="YjczY2JkNWY3NjE4NDAyOTkyMmRiZjc0MDAzYmVjOTk4M"
    api_key = "ODkyZGNlY2Y1NTZmNGRjYTljZWFjZmUzZDAwZTAyMGI5N"
    authobj = {  
        'api_key': api_key,  
        'upn': user,  
        'timestamp': str(int(time.time() * 1000)),  
        'signature_method': 'HMAC-SHA1',  
        'api_version': '1.0'  
    }
    my_hash = hmac.new(secret, digestmod=hashlib.sha1) 
    my_hash.update(authobj['api_key'] + authobj['upn'] + authobj['timestamp'])
    authobj['signature'] = my_hash.hexdigest()
    auth_info_and_server = {"url": gateone_server, "auth": authobj}
    valid_json_auth_info = json.dumps(auth_info_and_server)
    return HttpResponse(valid_json_auth_info)



@permission_required('assets.add_asset', login_url='/auth_error/')
def access_server(request,uuid):
    """web方式登录remote主机"""
    server = get_object_or_404(Server,pk=uuid)
    host_ip = server.ssh_host
    host_user = server.ssh_user
    host_port = server.ssh_port
    host_password = server.ssh_password
    host_id = uuid

    return render(request,'assets/access_server.html', locals())


## 服务器信息
@permission_required('assets.add_asset', login_url='/auth_error/')
def server_add(request):
    sf = ServerForm()
    af = AssetForm()
    projects = Project.objects.all()
    services = Service.objects.all()
    ff_error = []
    if request.method == 'POST':
        af = AssetForm(request.POST)
        sf = ServerForm(request.POST)
        ip = request.POST.get('ssh_host', '')
        if Server.objects.filter(ssh_host=ip):
            ff_error.append(u'添加失败, 该IP %s 已存在!' % ip)
            return render(request,'assets/server_add.html', locals())
        if all((af.is_valid(),sf.is_valid())):
            asset_data = af.save(commit=False)
            asset_data.asset_type = "serverhost"
            asset_data.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            ##网卡
            nic_name0 = request.POST.get('nic_name0', '')
            if nic_name0:
                for i in range(6):
                    nic_name = "nic_name" + str(i)
                    nic_name = request.POST.get(nic_name)
                    nic_ipaddress = "nic_ipaddress" + str(i)
                    nic_ipaddress = request.POST.get(nic_ipaddress)
                    if nic_name and nic_ipaddress:
                        NIC.objects.create(asset = asset_data,name=nic_name,ipaddress=nic_ipaddress)
            obj = server_data
            return render(request,'assets/asset_success.html', locals())
        else:
            ff_error.append("关键信息遗漏或格式错误")
    return render(request,'assets/server_add.html', locals())

@permission_required('assets.add_asset', login_url='/auth_error/')
def server_list(request):
    servers = [i for i in Server.objects.all().order_by("-ssh_host") if i.asset.status=="on"]
    return render(request,'assets/server_list.html', locals())

@permission_required('assets.add_asset', login_url='/auth_error/')
def virtual_add(request):
    sf = ServerForm()
    af = AssetForm()
    projects = Project.objects.all()
    services = Service.objects.all()
    ff_error = []
    if request.method == 'POST':
        af = AssetForm(request.POST)
        sf = ServerForm(request.POST)
        ip = request.POST.get('ssh_host', '')
        if Server.objects.filter(ssh_host=ip):
            ff_error.append(u'添加失败, 该IP %s 已存在!' % ip)
            return render(request,'assets/virtual_add.html', locals())
        if all((af.is_valid(),sf.is_valid())):
            asset_data = af.save(commit=False)
            asset_data.asset_type = "virtual"
            asset_data.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            ## 网卡信息，好low啊，假装一台机器最多只有6个网卡
            nic_name0 = request.POST.get('nic_name0', '')
            if nic_name0:
                for i in range(6):
                    nic_name = "nic_name" + str(i)
                    nic_name = request.POST.get(nic_name)
                    nic_ipaddress = "nic_ipaddress" + str(i)
                    nic_ipaddress = request.POST.get(nic_ipaddress)
                    if nic_name and nic_ipaddress:
                        NIC.objects.create(asset = asset_data,name=nic_name,ipaddress=nic_ipaddress)
            obj = server_data
            return render(request,'assets/asset_success.html', locals())
        else:
            ff_error.append("关键信息遗漏或格式错误")
    return render(request,'assets/virtual_add.html', locals())


@permission_required('assets.add_asset', login_url='/auth_error/')
def server_detail(request,uuid):
    """ 物理主机详情 """
    server = get_object_or_404(Server, uuid=uuid)
    virtuals = Server.objects.filter(parent=server)
    asset = server.asset
    nic_data = NIC.objects.filter(asset=asset)
    # host_record = HostRecord.objects.filter(host=host).order_by('-time')
    return render(request,'assets/server_detail.html', locals())

@permission_required('assets.add_asset', login_url='/auth_error/')
def virtual_detail(request,uuid):
    """ 虚拟主机详情 """
    server = get_object_or_404(Server, uuid=uuid)
    asset = server.asset
    try:
        nic_data = NIC.objects.filter(asset=asset)
    except:
        nic_data = []
    # host_record = HostRecord.objects.filter(host=host).order_by('-time')
    return render(request,'assets/virtual_detail.html', locals())

###编辑物理主机信息###
@permission_required('assets.change_asset', login_url='/auth_error/')
def server_edit(request,uuid):
    # server = get_object_or_404(Server, uuid=uuid)
    server = Server.objects.get(pk=uuid)
    asset = server.asset
    af = AssetForm(instance=asset)
    sf = ServerForm(instance=server)
    nic = NIC.objects.filter(asset=asset)

    project_all = Project.objects.all()
    project_host = server.project.all()
    projects = [p for p in project_all if p not in project_host]

    service_all = Service.objects.all()
    service_host = server.service.all()
    services = [s for s in service_all if s not in service_host]

    if request.method == 'POST':
        af = AssetForm(request.POST, instance=asset)
        sf = ServerForm(request.POST, instance=server)
        if all((af.is_valid(),sf.is_valid())):
            asset_data = af.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/server_edit.html', locals())

###编辑虚拟主机信息###
@permission_required('assets.change_asset', login_url='/auth_error/')
def virtual_edit(request,uuid):
    server = get_object_or_404(Server, uuid=uuid)
    asset = server.asset
    af = AssetForm(instance=asset)
    sf = ServerForm(instance=server)
    nic = NIC.objects.filter(asset=asset)

    project_all = Project.objects.all()
    project_host = server.project.all()
    projects = [p for p in project_all if p not in project_host]

    service_all = Service.objects.all()
    service_host = server.service.all()
    services = [s for s in service_all if s not in service_host]

    if request.method == 'POST':
        af = AssetForm(request.POST, instance=asset)
        sf = ServerForm(request.POST, instance=server)
        if all((af.is_valid(),sf.is_valid())):
            asset_data = af.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/virtual_edit.html', locals())

##网卡操作11
@permission_required('assets.add_asset', login_url='/auth_error/')
def nic_add(request,uuid):
    asset_data = Asset.objects.get(uuid=uuid)
    nf = NICForm()
    error_information = []
    if request.method == 'POST':
        mac = request.POST.get('ipaddress', '')
        if mac:
            nf = NICForm(request.POST)
            if nf.is_valid():
                nic_data = nf.save(commit=False)
                nic_data.asset = asset_data
                nic_data.save()

    return render(request,'assets/nic_add.html', locals())

@permission_required('assets.add_asset', login_url='/auth_error/')
def nic_edit(request,uuid):
    nic_data = NIC.objects.get(pk=uuid)
    nf = NICForm(instance=nic_data)
    if request.method == 'POST':
        mac = request.POST.get('ipaddress', '')
        if mac:
            nf = NICForm(request.POST,instance=nic_data)
            if nf.is_valid():
                nic_data = nf.save()

    return render(request,'assets/nic_edit.html', locals())

@permission_required('assets.delete_Asset', login_url='/auth_error/')
def nic_delete(request,uuid):
    nic_data = NIC.objects.get(pk=uuid)
    nic_data.delete()

    return HttpResponse('Delete Success!')

##内存条操作
# @permission_required('assets.add_asset', login_url='/auth_error/')
# def ram_add(request,uuid):
#     asset_data = Asset.objects.get(uuid=uuid)
#     rf = RAMForm()
#     ram_error_information = []
#     if request.method == 'POST':
#         capacity = request.POST.get('capacity', '')
#         if capacity:
#             rf = RAMForm(request.POST)
#             if rf.is_valid():
#                 ram_data = rf.save(commit=False)
#                 ram_data.asset = asset_data
#                 ram_data.save()
#                 return HttpResponse('ADD Success!')

#     return render(request,'assets/ram_add.html', locals())

# @permission_required('assets.add_asset', login_url='/auth_error/')
# def ram_edit(request,uuid):
#     ram_data = RAM.objects.get(pk=uuid)
#     rf = RAMForm(instance=ram_data)
#     if request.method == 'POST':
#         capacity = request.POST.get('capacity', '')
#         if capacity:
#             rf = RAMForm(request.POST,instance=ram_data)
#             if rf.is_valid():
#                 ram_data = rf.save()

#     return render(request,'assets/ram_edit.html', locals())

# @permission_required('assets.delete_asset', login_url='/auth_error/')
# def ram_delete(request,uuid):
#     ram_data = RAM.objects.get(pk=uuid)
#     ram_data.delete()

#     return HttpResponse('Delete Success!')

# ##硬盘信息
# @permission_required('assets.add_asset', login_url='/auth_error/')
# def disk_add(request,uuid):
#     asset_data = Asset.objects.get(uuid=uuid)
#     diskf = DiskForm()
#     disk_error_information = []
#     if request.method == 'POST':
#         capacity = request.POST.get('capacity', '')
#         if capacity:
#             diskf = DiskForm(request.POST)
#             if diskf.is_valid():
#                 disk_data = diskf.save(commit=False)
#                 disk_data.asset = asset_data
#                 disk_data.save()
#                 return HttpResponse('ADD Success!')

#     return render(request,'assets/disk_add.html', locals())

# @permission_required('assets.add_asset', login_url='/auth_error/')
# def disk_edit(request,uuid):
#     disk_data = Disk.objects.get(pk=uuid)
#     diskf = DiskForm(instance=disk_data)
#     if request.method == 'POST':
#         capacity = request.POST.get('capacity', '')
#         if capacity:
#             diskf = DiskForm(request.POST,instance=disk_data)
#             if diskf.is_valid():
#                 disk_data = diskf.save()

#     return render(request,'assets/disk_edit.html', locals())

# @permission_required('assets.delete_asset', login_url='/auth_error/')
# def disk_delete(request,uuid):
#     disk_data = Disk.objects.get(pk=uuid)
#     disk_data.delete()

#     return HttpResponse('Delete Success!')

# ##raid卡
# @permission_required('assets.add_asset', login_url='/auth_error/')
# def raid_add(request,uuid):
#     asset_data = Asset.objects.get(uuid=uuid)
#     raidf = RaidForm()
#     raid_error_information = []
#     if request.method == 'POST':
#         model = request.POST.get('model', '')
#         if model:
#             raidf = RaidForm(request.POST)
#             if raidf.is_valid():
#                 raid_data = raidf.save(commit=False)
#                 raid_data.asset = asset_data
#                 raid_data.save()
#                 return HttpResponse('ADD Success!')

#     return render(request,'assets/raid_add.html', locals())

# @permission_required('assets.add_asset', login_url='/auth_error/')
# def raid_edit(request,uuid):
#     raid_data = RaidAdaptor.objects.get(pk=uuid)
#     raidf = RaidForm(instance=raid_data)
#     if request.method == 'POST':
#         model = request.POST.get('model', '')
#         if model:
#             raidf = RaidForm(request.POST,instance=raid_data)
#             if raidf.is_valid():
#                 raid_data = raidf.save()

#     return render(request,'assets/raid_edit.html', locals())

# @permission_required('assets.delete_asset', login_url='/auth_error/')
# def raid_delete(request,uuid):
#     raid_data = RaidAdaptor.objects.get(pk=uuid)
#     raid_data.delete()

#     return HttpResponse('Delete Success!')

def look_server_passwd(request,uuid):
    data = Server.objects.get(pk=uuid)
    nic_data = NIC.objects.filter(asset=data.asset)
    sql_data = sqlpasswd.objects.filter(server=data)
    return render(request,'assets/passwd_list.html', locals()) 

@permission_required('assets.add_sqlpasswd', login_url='/auth_error/')
def add_sql_passwd(request,uuid):
    uuid = uuid
    server = Server.objects.get(pk=uuid)
    sf = SQLpassForm()
    if request.method == 'POST':
        sf = SQLpassForm(request.POST)
        if sf.is_valid():
            data = sf.save(commit=False)
            data.server = server
            data.save()
            return HttpResponse('ADD Success!')

    return render(request,'assets/passwd_add.html', locals()) 

@permission_required('assets.add_sqlpasswd', login_url='/auth_error/')
def modify_sql_passwd(request,uuid):
    server = Server.objects.get(pk=uuid)
    sql_data = sqlpasswd.objects.filter(server=server)
    if request.method == 'POST':
        data = json.loads(request.body)
        if data['name'] == "host":
            Server.objects.filter(pk=uuid).update(ssh_password=data['server_pass'],ssh_user=data['server_user'],ssh_port=data['server_port'])
            return JsonResponse({'status':"OK",'info':"主机权限已更改！"})
        if data['name'] == "sqlpass":
            sqlpasswd.objects.filter(pk=data['sqlpass_id']).update(title=data['title'],listen=data['listen'],port=data['port'],user=data['user'],dbname=data['dbname'],memo=data['memo'],password=data['password'])
            return JsonResponse({'status':"OK",'info':"数据库权限已更改！"})
        if data['name'] == "delete":
            sqlpasswd.objects.get(pk=data['sqlpass_id']).delete()
            return JsonResponse({'status':"OK",'info':"数据库权限已删除！"})
        return JsonResponse({'status':"ERROR",'info':"wrong!"})

    return render(request,'assets/passwd_modify.html', locals())




@permission_required('assets.add_sqlpasswd', login_url='/auth_error/')
def pull_server_information(request,uuid):
    #"""自动拉取服务器的配置信息"""
    # uuid = request.GET.get('uuid', '')
    data = Server.objects.get(pk=uuid)
    asset_type = data.asset.asset_type
    ip = data.ssh_host
    port = data.ssh_port
    user = data.ssh_user
    password = data.ssh_password
    L = [ip,port,user,password,uuid]
    errors_info = []
    if '' in L:
        errors_info.append("服务器ssh信息不完整！")

    if errors_info:
        if asset_type == "virtual":
            return HttpResponseRedirect('/assets/virtual_detail/' + '%s' % uuid)
        else:
            return HttpResponseRedirect('/assets/server_detail/' + '%s' % uuid)
    else:
        aa = asset_ansible_update([data],asset_type)
        if asset_type == "virtual":
            return HttpResponseRedirect('/assets/virtual_detail/' + '%s' % uuid)
        else:
            return HttpResponseRedirect('/assets/server_detail/' + '%s' % uuid)

from .tasks import init_sys
from celery.result import AsyncResult


@permission_required('assets.add_asset', login_url='/auth_error/')
def initialization_system(request,uuid):
    """系统初始化"""
    server_id = uuid
    if request.method =='POST':
        data = Server.objects.get(pk=uuid)
        obj = init_sys.delay(uuid)
        task_id = obj.id
        print task_id
    return render(request,'assets/progress_bar.html',locals())


def modify_password(request):
    if request.method =='POST':
        host_ip = request.POST.get('ip')
        password = request.POST.get('password')
        print host_ip,password
        try:
            a = Server.objects.filter(ssh_host=host_ip)
            if a:
                a.update(ssh_password=password)
            else:
                print "没有此ip：%s,开始创建数据"% host_ip
                adata = Asset(asset_type='virtual',purpose="nothing")
                adata.save()
                vdata = Server(asset=adata,ssh_host=host_ip,ssh_port="22992",ssh_user="root",ssh_password=password)
                vdata.save()
        except:
            print "没有此ip：%s"% host_ip
    return HttpResponse("OK")

# def organize_data(group):
#     data = Project.objects.filter(parent=group)
#     servers = group.project_servers.all()
#     if servers:
#         server = [{"name":i.ssh_host} for i in servers]
#     else:
#         server = []
#     res = {"name":group.project_name,"children":server}
#     L = []
#     print "开支组装组：%s"% group.project_name
#     if data:
#         print "有分支"
#         for i in data:
#             L.append(organize_data(i))
#         res["children"] = server + L
#     return res

def znodes(groups):
    L = []
    gservers = []
    for i in groups:
        name = i.project_name
        uuid = str(i.uuid)
        if i.parent:
            L.append({"name":name,"id":uuid,"pid":str(i.parent.uuid),"isParent":"true","isproject":"yes"})
        else:
            L.append({"name":name,"id":uuid,"pid": 0,"isParent":"true","open":"true","isproject":"yes"})
        servers = i.project_servers.all()
        if servers:
            for server in servers:
                gservers.append(server)
                L.append({"name":server.ssh_host,"id":str(server.uuid),"pid":uuid,"isParent":"false","dropInner":"false","isproject":"no"})
    L = L + [{"name":i.ssh_host,"id":str(i.uuid),"pid":0,"isParent":"false","dropInner":"false","isproject":"no"} for i in Server.objects.all() if i not in gservers]
    return L

def group_tree(request):
    groups = Project.objects.all()
    res = []
    res = znodes(groups)
    return JsonResponse({"data":res},safe=False)

def vps_list(request):
    try:  
        page = int(request.GET.get("page",1))
        if page < 1:  
            page = 1  
    except ValueError:  
        page = 1
    data = Server.objects.all()
    paginator = JuncheePaginator(data, 10)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)
    return render(request,'assets/vps_list.html',locals())

def vps_search(request):
    result = {}
    comment = request.GET.get("comment")
    print comment
    dataA = Server.objects.filter(project__project_name__contains=comment) #根据project关键字获取server集合
    dataB = Server.objects.filter(ssh_host__contains=comment) #ssh_host关键字查找
    dataC = [ i.asset.server for i in NIC.objects.filter(ipaddress__contains=comment) if i] #网卡ip过滤
    dataD = [i.server for i in Asset.objects.filter(purpose__contains=comment) if i] #purpose用途过滤
    res = list(set(dataA)|set(dataB)|set(dataC)|set(dataD))
    if res:
        ff = []
        for i in res:
            projects = i.project.all()
            phtml = ""
            if projects:
                for p in projects:
                    phtml = phtml + "<a class='btn btn-primary btn-xs'>"+p.project_name+"</a>"
            nic = ""
            for n in i.asset.wangka.all():
                if n.ipaddress:
                    if n.name:
                        nic=nic+n.name+":"+n.ipaddress+"<br>"
                    else:
                        nic = nic+"eth0:"+n.ipaddress+"<br>"
            status = "<p class='text-danger'>报废</p>"
            if i.asset.status == 'on':
                status = "<p class='text-success'>线上</p>"
            opreation = """
            <a href="/assets/add_sql_passwd/%s" class="btn btn-default btn-xs addpasswd" data-toggle="tooltip" title="添加权限"><i class="fa fa-plus"></i></a>
            <a href="/assets/modify_sql_passwd/%s" class="btn btn-default btn-xs changepasswd" data-toggle="tooltip" title="修改权限密码"><i class="fa fa-pencil-square-o"></i></a>
            <a href="/assets/look_server_passwd/%s" class="btn btn-default btn-xs lookpasswd" data-toggle="tooltip" title="查看权限"><i class="fa fa-eye"></i></a>
            """% (i.uuid,i.uuid,i.uuid)
            if i.asset.asset_type == 'serverhost':
                details ="""<a href="/assets/server_detail/%s" target="_blank" class="btn btn-info btn-xs" style="color: black"><i class="fa fa-asterisk"></i>详情</a>"""% i.uuid
            else:
                details ="""<a href="/assets/virtual_detail/%s" target="_blank" class="btn btn-info btn-xs" style="color: black"><i class="fa fa-asterisk"></i>详情</a>"""% i.uuid
            ff.append({"group":phtml,"ssh_host":i.ssh_host,"nic":nic,"purpose":i.asset.purpose,"status":status,"uuid":i.uuid,"opreation":opreation,"details":details})
        result["res"] = "OK"
        result["info"] = ff
    else:
        result["res"] = "Faild"

    return JsonResponse(result,safe=False)

