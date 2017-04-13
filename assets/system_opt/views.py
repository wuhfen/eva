#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.db.models.base import ObjectDoesNotExist

from assets.models import publickey,zabbixagent,Server,basepkg,Asset
from assets.system_opt.forms import pubkeyForm, zabbixagentForm, basepkgForm
# Create your views here.
from assets.ansible_update_assert import asset_ansible_update
from api.common_api import create_ansible_inventory,gen_resource
from api.ansible_api import MyRunner,MyTask,MyPlayTask
import re
import traceback
import json

@permission_required('assets.add_Asset', login_url='/auth_error/')
def system_init(request):
    pubkey_data = publickey.objects.all()
    zabbix_data = zabbixagent.objects.all()
    basepkg_data = basepkg.objects.all()
    if request.method == 'POST':
        check_box_list = request.POST.getlist('check_box_list')
        server_list = [x for x in request.POST.get('servers').split('\r\n') if x ]
        if not server_list:
            return HttpResponse("你没有给出服务器")
        try:
            obj_list = [Server.objects.get(ssh_host=host) for host in server_list if host]
        except ObjectDoesNotExist:
            some_infomation = server_list
            return render(request,'default/reminder.html',locals())
        resource = gen_resource(obj_list)
        ansible_instance = MyTask(resource)
        ansible_playtask = MyPlayTask(resource)

        if "pubkey" in check_box_list:
            pubkey_uuid = request.POST.get('public_key')
            pubkey_use_obj = publickey.objects.get(pk=pubkey_uuid)

            user ='root'
            key = pubkey_use_obj.pubkey

            ansible_auth = ansible_instance.push_key(user, key)

        if "selinux" in check_box_list:
            selinux_state = request.POST.get('selinux_state','')
            ansible_selinux = ansible_instance.set_selinux(selinux_state)

        if "install_base_pkg" in check_box_list:
            pkg_id = request.POST.get('base_pkg','')
            print pkg_id
            print type(pkg_id)

            # pkgs = basepkg.objects.get(pk=pkg_id)
            # print pkgs.toollist


        if "install_zabbix_agent" in check_box_list:
            zabbix_uuid = request.POST.get('zabbix_agent','')
            zabbix_obj = zabbixagent.objects.get(pk=zabbix_uuid)

            version = zabbix_obj.version
            listenip = zabbix_obj.listenip
            listenport = zabbix_obj.listenport
            server = zabbix_obj.server
            serveractive = zabbix_obj.serveractive

            zabbix_agent_install =  ansible_playtask.install_zabbix_agent(version,server,listenport,listenip,serveractive)
        return HttpResponseRedirect('/allow/welcome/')

    return render(request,'assets/system_init.html',locals())

@permission_required('assets.add_Asset', login_url='/auth_error/')
def public_key_add(request):
    pf = pubkeyForm()
    if request.method == 'POST':
        pf = pubkeyForm(request.POST)
        if pf.is_valid():
            data = pf.save()
            return HttpResponseRedirect('/assets/system/publickey/list/')
    return render(request,'assets/publickey_add.html',locals())

@permission_required('assets.add_Asset', login_url='/auth_error/')
def public_key_list(request):
    data = publickey.objects.all()
    return render(request,'assets/publickey_list.html',locals())

@permission_required('assets.add_Asset', login_url='/auth_error/')
def public_key_delete(request,uuid):
    data = get_object_or_404(publickey,pk=uuid)
    data.delete()
    return HttpResponse("DELETE SUCCESS!")

@permission_required('assets.add_Asset', login_url='/auth_error/')
def zabbix_agent_add(request):
    pf = zabbixagentForm()
    if request.method == 'POST':
        pf = zabbixagentForm(request.POST)
        if pf.is_valid():
            data = pf.save()
            return HttpResponseRedirect('/assets/system/zabbix_agent/list/')
    return render(request,'assets/zabbix_agent_add.html',locals())

@permission_required('assets.add_Asset', login_url='/auth_error/')
def zabbix_agent_list(request):
    data = zabbixagent.objects.all()
    return render(request,'assets/zabbixagent_list.html',locals())

@permission_required('assets.add_Asset', login_url='/auth_error/')
def zabbix_agent_delete(request,uuid):
    data = get_object_or_404(zabbixagent,pk=uuid)
    data.delete()
    return HttpResponse("DELETE SUCCESS!")

@permission_required('assets.add_basepkg', login_url='/auth_error/')
def basepkg_list(request):
    data = basepkg.objects.all()
    return render(request,'assets/basepkg_list.html',locals())

@permission_required('assets.add_basepkg', login_url='/auth_error/')
def basepkg_add(request):
    pf = basepkgForm()
    if request.method == 'POST':
        pf = basepkgForm(request.POST)
        if pf.is_valid():
            data = pf.save()
            return HttpResponseRedirect('/assets/system/basepkg/list/')
    return render(request,'assets/basepkg_add.html',locals())

@permission_required('assets.add_basepkg', login_url='/auth_error/')
def basepkg_delete(request,id):
    data = get_object_or_404(basepkg,pk=id)
    data.delete()
    return HttpResponse("DELETE SUCCESS!")



####下面是服务器批量操作和导入导出的views
@permission_required('assets.add_Asset',login_url='/auth_error/')
def batch_pull_infomation(request):
    """批量拉取服务器最新配置信息"""
    if "name" in request.GET and request.GET['name'] == "okk":
        for x in [Server.objects.get(pk=i) for i in request.GET['cbvs'].strip(',').split(',')]: asset_ansible_update([x],x.asset.asset_type)
    return JsonResponse({'status':"OK",'info':"已全部更新完成"})

def pings(host):
    resource = gen_resource(host)
    ansible_instance = MyTask(resource)
    res = {}
    print ansible_instance.check_vm()
    if ansible_instance.check_vm()['hosts'][host.ssh_host].has_key('ping'):
        res = {host.ssh_host:"pong"}
        Asset.objects.filter(pk=host.asset.uuid).update(mark=True)
    else:
        res[host.ssh_host]="fail"
        Asset.objects.filter(pk=host.asset.uuid).update(mark=False)
    return res

@permission_required('assets.add_Asset',login_url='/auth_error/')
def batch_ping(request):
    """探测主机是否可用"""
    if "name" in request.GET and request.GET['name'] == "ping":
        info = map(pings,[Server.objects.get(pk=i) for i in request.GET['cbvs'].strip(',').split(',')])
        print info
        return JsonResponse({'status':"OK",'info': json.dumps(info)})
    return JsonResponse({'status':"OKd",'info':"可用"})

@permission_required('assets.add_Asset',login_url='/auth_error/')
def batch_add_vm(request):
    return render(request,'assets/batch_add_vm.html',locals())