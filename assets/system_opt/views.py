#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from assets.models import publickey,zabbixagent,Server
from assets.system_opt.forms import pubkeyForm, zabbixagentForm
# Create your views here.

from api.common_api import create_ansible_inventory,gen_resource
from api.ansible_api import MyRunner,MyTask,MyPlayTask
import re
import traceback

@permission_required('assets.add_Asset', login_url='/auth_error/')
def system_init(request):
    pubkey_data = publickey.objects.all()
    zabbix_data = zabbixagent.objects.all()
    if request.method == 'POST':
        check_box_list = request.POST.getlist('check_box_list')
        server_list = [x for x in request.POST.get('servers').split('\r\n') if x ]
        obj_list = [Server.objects.get(ssh_host=host) for host in server_list if host]
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