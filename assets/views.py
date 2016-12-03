#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from assets.models import IDC, Service, Line, Project
from assets.models import Asset, Server, NIC, RaidAdaptor, Disk, CPU, RAM
from forms import ServerForm, AssetForm, CPUForm, RAMForm, DiskForm, NICForm, RaidForm
# Create your views here.

import re

def isValidIp(ip):  
    if re.match(r"^\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$", ip): return True  
    return False  
      
def isValidMac(mac):  
    if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac): return True  
    return False 

##还没有对网卡输入的IP与mac进行验证，上面定义两个函数，有时间在进行处理，最好使用前端js进行验证，不用后端处理



## 服务器信息
@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def server_add(request):
    sf = ServerForm()
    af = AssetForm()
    cf = CPUForm()
    projects = Project.objects.all()
    services = Service.objects.all()
    ff_error = []
    if request.method == 'POST':
        af = AssetForm(request.POST)
        sf = ServerForm(request.POST)
        cf = CPUForm(request.POST)
        ip = request.POST.get('ssh_host', '')
        if Server.objects.filter(ssh_host=ip):
            ff_error.append(u'添加失败, 该IP %s 已存在!' % ip)
            return render(request,'assets/server_add.html', locals())
        if all((af.is_valid(),sf.is_valid(),cf.is_valid())):
            asset_data = af.save()
            cpu_data = cf.save(commit=False)
            cpu_data.asset = asset_data
            cpu_data.save()
            cf.save_m2m()
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

                    nic_memo = "nic_memo" + str(i)
                    nic_memo = request.POST.get(nic_memo)

                    nic_macaddress = "nic_macaddress" + str(i)
                    nic_macaddress = request.POST.get(nic_macaddress)

                    nic_ipaddress = "nic_ipaddress" + str(i)
                    nic_ipaddress = request.POST.get(nic_ipaddress)

                    nic_netmask = "nic_netmask" + str(i)
                    nic_netmask = request.POST.get(nic_netmask)

                    nic_model = "nic_model" + str(i)
                    nic_model = request.POST.get(nic_model)

                    if nic_name and nic_macaddress:
                        NIC.objects.create(asset = asset_data,name=nic_name,model=nic_model,macaddress=nic_macaddress,
                        ipaddress=nic_ipaddress,netmask=nic_netmask,memo=nic_memo)
            return HttpResponseRedirect('/allow/welcome/')
## 内存
            ram_model0 = request.POST.get('ram_model0', '')
            if ram_model0:
                for i in range(16):
                    ram_model = "ram_model" + str(i)
                    ram_model = request.POST.get(ram_model)

                    ram_slot = "ram_slot" + str(i)
                    ram_slot = request.POST.get(ram_slot)

                    ram_capacity = "ram_capacity" + str(i)
                    ram_capacity = request.POST.get(ram_capacity)

                    ram_sn = "ram_sn" + str(i)
                    ram_sn = request.POST.get(ram_sn)

                    ram_memo = "ram_memo" + str(i)
                    ram_memo = request.POST.get(ram_memo)

                    if ram_model and ram_capacity:
                        RAM.objects.create(asset = asset_data,model=ram_model,slot=ram_slot,
                        capacity=ram_capacity,sn=ram_sn,memo=ram_memo)
##硬盘
            disk_model0 = request.POST.get('disk_model0', '')
            if disk_model0:
                for i in range(12):
                    disk_model = "disk_model" + str(i)
                    disk_model = request.POST.get(disk_model)

                    disk_manufactory = "disk_manufactory" + str(i)
                    disk_manufactory = request.POST.get(disk_manufactory)

                    disk_capacity = "disk_capacity" + str(i)
                    disk_capacity = request.POST.get(disk_capacity)

                    disk_iface_type = "disk_iface_type" + str(i)
                    disk_iface_type = request.POST.get(disk_iface_type)

                    disk_slot = "disk_slot" + str(i)
                    disk_slot = request.POST.get(disk_slot)

                    disk_sn = "disk_sn" + str(i)
                    disk_sn = request.POST.get(disk_sn)

                    disk_memo = "disk_memo" + str(i)
                    disk_memo = request.POST.get(disk_memo)

                    if disk_model and disk_capacity:
                        Disk.objects.create(asset = asset_data,model=disk_model,manufactory=disk_manufactory,iface_type=disk_iface_type,slot=disk_slot,
                        capacity=disk_capacity,sn=disk_sn,memo=disk_memo)
##raid卡
            raid_model0 = request.POST.get('raid_model0', '')
            if raid_model0:
                for i in range(2):
                    raid_model = "raid_model" + str(i)
                    raid_model = request.POST.get(raid_model)

                    raid_slot = "raid_slot" + str(i)
                    raid_slot = request.POST.get(raid_slot)

                    raid_sn = "raid_sn" + str(i)
                    raid_sn = request.POST.get(raid_sn)

                    raid_memo = "raid_memo" + str(i)
                    raid_memo = request.POST.get(raid_memo)

                    if raid_model and raid_slot:
                        RaidAdaptor.objects.create(asset = asset_data,model=raid_model,slot=raid_slot,
                        sn=raid_sn,memo=raid_memo)

            return HttpResponseRedirect('/allow/welcome/')
        else:
            ff_error.append("关键信息遗漏或格式错误")
    return render(request,'assets/server_add.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def server_list(request):
    # assets = Asset.objects.all()
    # assets = Asset.objects.get(asset_number="DT-test-02932")
    servers = Server.objects.all().order_by("-ssh_host")
    # servers = Server.objects.get(name="ggg-003")
    # return HttpResponse(servers.asset.nic)
    return render(request,'assets/server_list.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def virtual_add(request):
    sf = ServerForm()
    af = AssetForm()
    cf = CPUForm()
    projects = Project.objects.all()
    services = Service.objects.all()
    ff_error = []
    if request.method == 'POST':
        af = AssetForm(request.POST)
        sf = ServerForm(request.POST)
        cf = CPUForm(request.POST)
        ip = request.POST.get('ssh_host', '')
        if Server.objects.filter(ssh_host=ip):
            ff_error.append(u'添加失败, 该IP %s 已存在!' % ip)
            return render(request,'assets/virtual_add.html', locals())
        if all((af.is_valid(),sf.is_valid(),cf.is_valid())):
            asset_data = af.save(commit=False)
            asset_data.asset_type = "virtual"
            asset_data.save()
            cpu_data = cf.save(commit=False)
            cpu_data.asset = asset_data
            cpu_data.save()
            cf.save_m2m()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
## 网卡信息
            nic_name0 = request.POST.get('nic_name0', '')
            if nic_name0:
                for i in range(6):
                    nic_name = "nic_name" + str(i)
                    nic_name = request.POST.get(nic_name)

                    nic_memo = "nic_memo" + str(i)
                    nic_memo = request.POST.get(nic_memo)

                    nic_macaddress = "nic_macaddress" + str(i)
                    nic_macaddress = request.POST.get(nic_macaddress)

                    nic_ipaddress = "nic_ipaddress" + str(i)
                    nic_ipaddress = request.POST.get(nic_ipaddress)

                    nic_netmask = "nic_netmask" + str(i)
                    nic_netmask = request.POST.get(nic_netmask)

                    if nic_name and nic_macaddress:
                        NIC.objects.create(asset = asset_data,name=nic_name,macaddress=nic_macaddress,
                        ipaddress=nic_ipaddress,netmask=nic_netmask,memo=nic_memo)
            return HttpResponseRedirect('/allow/welcome/')
        else:
            ff_error.append("关键信息遗漏或格式错误")
    return render(request,'assets/virtual_add.html', locals())


@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def server_detail(request,uuid):
    """ 物理主机详情 """
    server = get_object_or_404(Server, uuid=uuid)
    virtuals = Server.objects.filter(parent=server)
    asset = server.asset
    cpu_data = asset.cpu
    ram_data = RAM.objects.filter(asset=asset)
    disk_data = Disk.objects.filter(asset=asset)
    raid_data = RaidAdaptor.objects.filter(asset=asset)
    nic_data = NIC.objects.filter(asset=asset)
    # host_record = HostRecord.objects.filter(host=host).order_by('-time')

    return render(request,'assets/server_detail.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def virtual_detail(request,uuid):
    """ 虚拟主机详情 """
    server = get_object_or_404(Server, uuid=uuid)
    asset = server.asset
    cpu_data = asset.cpu
    nic_data = NIC.objects.filter(asset=asset)
    # host_record = HostRecord.objects.filter(host=host).order_by('-time')

    return render(request,'assets/virtual_detail.html', locals())

###编辑物理主机信息###
@permission_required('assets.Can_change_Asset', login_url='/auth_error/')
def server_edit(request,uuid):
    # server = get_object_or_404(Server, uuid=uuid)
    server = Server.objects.get(pk=uuid)
    asset = server.asset
    cpu = asset.cpu
    cf = CPUForm(instance=cpu)
    af = AssetForm(instance=asset)
    sf = ServerForm(instance=server)

    nic = NIC.objects.filter(asset=asset)
    ram = RAM.objects.filter(asset=asset)
    disk = Disk.objects.filter(asset=asset)
    raid = RaidAdaptor.objects.filter(asset=asset)

    project_all = Project.objects.all()
    project_host = server.project.all()
    projects = [p for p in project_all if p not in project_host]

    service_all = Service.objects.all()
    service_host = server.service.all()
    services = [s for s in service_all if s not in service_host]

    if request.method == 'POST':
        af = AssetForm(request.POST, instance=asset)
        sf = ServerForm(request.POST, instance=server)
        cf = CPUForm(request.POST, instance=cpu)

        if all((af.is_valid(),sf.is_valid(),cf.is_valid())):
            asset_data = af.save()
            cpu_data = cf.save(commit=False)
            cpu_data.asset = asset_data
            cpu_data.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/server_edit.html', locals())

###编辑虚拟主机信息###
@permission_required('assets.Can_change_Asset', login_url='/auth_error/')
def virtual_edit(request,uuid):
    server = get_object_or_404(Server, uuid=uuid)
    asset = server.asset
    cpu = asset.cpu
    cf = CPUForm(instance=cpu)
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
        cf = CPUForm(request.POST, instance=cpu)

        if all((af.is_valid(),sf.is_valid(),cf.is_valid())):
            asset_data = af.save()
            cpu_data = cf.save(commit=False)
            cpu_data.asset = asset_data
            cpu_data.save()
            server_data = sf.save(commit=False)
            server_data.asset = asset_data
            server_data.save()
            sf.save_m2m()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/virtual_edit.html', locals())

##网卡操作
@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def nic_add(request,uuid):
    asset_data = Asset.objects.get(uuid=uuid)
    nf = NICForm()
    error_information = []
    if request.method == 'POST':
        mac = request.POST.get('macaddress', '')
        if mac:
            nf = NICForm(request.POST)
            if nf.is_valid():
                nic_data = nf.save(commit=False)
                nic_data.asset = asset_data
                nic_data.save()

    return render(request,'assets/nic_add.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def nic_edit(request,uuid):
    nic_data = NIC.objects.get(pk=uuid)
    nf = NICForm(instance=nic_data)
    if request.method == 'POST':
        mac = request.POST.get('macaddress', '')
        if mac:
            nf = NICForm(request.POST,instance=nic_data)
            if nf.is_valid():
                nic_data = nf.save()

    return render(request,'assets/nic_edit.html', locals())

@permission_required('assets.Can_delete_Asset', login_url='/auth_error/')
def nic_delete(request,uuid):
    nic_data = NIC.objects.get(pk=uuid)
    nic_data.delete()

    return HttpResponse('Delete Success!')

##内存条操作
@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def ram_add(request,uuid):
    asset_data = Asset.objects.get(uuid=uuid)
    rf = RAMForm()
    ram_error_information = []
    if request.method == 'POST':
        capacity = request.POST.get('capacity', '')
        if capacity:
            rf = RAMForm(request.POST)
            if rf.is_valid():
                ram_data = rf.save(commit=False)
                ram_data.asset = asset_data
                ram_data.save()
                return HttpResponse('ADD Success!')

    return render(request,'assets/ram_add.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def ram_edit(request,uuid):
    ram_data = RAM.objects.get(pk=uuid)
    rf = RAMForm(instance=ram_data)
    if request.method == 'POST':
        capacity = request.POST.get('capacity', '')
        if capacity:
            rf = RAMForm(request.POST,instance=ram_data)
            if rf.is_valid():
                ram_data = rf.save()

    return render(request,'assets/ram_edit.html', locals())

@permission_required('assets.Can_delete_Asset', login_url='/auth_error/')
def ram_delete(request,uuid):
    ram_data = RAM.objects.get(pk=uuid)
    ram_data.delete()

    return HttpResponse('Delete Success!')

##硬盘信息
@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def disk_add(request,uuid):
    asset_data = Asset.objects.get(uuid=uuid)
    diskf = DiskForm()
    disk_error_information = []
    if request.method == 'POST':
        capacity = request.POST.get('capacity', '')
        if capacity:
            diskf = DiskForm(request.POST)
            if diskf.is_valid():
                disk_data = diskf.save(commit=False)
                disk_data.asset = asset_data
                disk_data.save()
                return HttpResponse('ADD Success!')

    return render(request,'assets/disk_add.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def disk_edit(request,uuid):
    disk_data = Disk.objects.get(pk=uuid)
    diskf = DiskForm(instance=disk_data)
    if request.method == 'POST':
        capacity = request.POST.get('capacity', '')
        if capacity:
            diskf = DiskForm(request.POST,instance=disk_data)
            if diskf.is_valid():
                disk_data = diskf.save()

    return render(request,'assets/disk_edit.html', locals())

@permission_required('assets.Can_delete_Asset', login_url='/auth_error/')
def disk_delete(request,uuid):
    disk_data = Disk.objects.get(pk=uuid)
    disk_data.delete()

    return HttpResponse('Delete Success!')

##raid卡
@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def raid_add(request,uuid):
    asset_data = Asset.objects.get(uuid=uuid)
    raidf = RaidForm()
    raid_error_information = []
    if request.method == 'POST':
        model = request.POST.get('model', '')
        if model:
            raidf = RaidForm(request.POST)
            if raidf.is_valid():
                raid_data = raidf.save(commit=False)
                raid_data.asset = asset_data
                raid_data.save()
                return HttpResponse('ADD Success!')

    return render(request,'assets/raid_add.html', locals())

@permission_required('assets.Can_add_Asset', login_url='/auth_error/')
def raid_edit(request,uuid):
    raid_data = RaidAdaptor.objects.get(pk=uuid)
    raidf = RaidForm(instance=raid_data)
    if request.method == 'POST':
        model = request.POST.get('model', '')
        if model:
            raidf = RaidForm(request.POST,instance=raid_data)
            if raidf.is_valid():
                raid_data = raidf.save()

    return render(request,'assets/raid_edit.html', locals())

@permission_required('assets.Can_delete_Asset', login_url='/auth_error/')
def raid_delete(request,uuid):
    raid_data = RaidAdaptor.objects.get(pk=uuid)
    raid_data.delete()

    return HttpResponse('Delete Success!')