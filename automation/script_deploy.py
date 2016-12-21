#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from tempfile import NamedTemporaryFile

from assets.models import Server

from automation.models import scriptrepo, scriptlog
from automation.forms import ScriptForm
from api.ansible_api import ansiblex_deploy
import time

@permission_required('automation.add_Tools', login_url='/auth_error/')
def add_script(request):
    sf = ScriptForm()
    if request.method == 'POST':
        sf = ScriptForm(request.POST)
        if sf.is_valid():
            sf.save()
            return HttpResponseRedirect('/deploy/script_list')
    
    return render(request,'automation/script_add.html',locals())



@permission_required('automation.add_Tools', login_url='/auth_error/')
def edit_script(request,uuid):
    data = scriptrepo.objects.get(pk=uuid)
    sf = ScriptForm(instance=data)
    if request.method == 'POST':
        sf = ScriptForm(request.POST,instance=data)
        if sf.is_valid():
            sf.save()
            return HttpResponseRedirect('/deploy/script_list')
    return render(request,'automation/script_edit.html',locals())


@permission_required('automation.add_Tools', login_url='/auth_error/')
def delete_script(request,uuid):
    data = scriptrepo.objects.get(pk=uuid)
    data.delete()
    return render(request,'automation/script_list.html',locals())

@permission_required('automation.add_Tools', login_url='/auth_error/')
def list_script(request):
    data = scriptrepo.objects.all()
    return render(request,'automation/script_list.html',locals())


def script_inventory(uuid,groupname):
    hostsFile = NamedTemporaryFile(delete=False)
    data = scriptrepo.objects.get(pk=uuid)
    group = "[%s]" % groupname
    L = [group]
    ip = data.server_ip
    i = Server.objects.get(ssh_host=ip)
    host = "%s ansible_ssh_port=%s ansible_ssh_use=%s ansible_ssh_pass=%s" % (i.ssh_host,i.ssh_port,i.ssh_user,i.ssh_password)
    L.append(host)
    for s in L:
        hostsFile.write(s+'\n')
    hostsFile.close()
    return hostsFile.name


@permission_required('automation.add_Tools', login_url='/auth_error/')
def deploy_script(request):
    data = scriptrepo.objects.all()
    now = int(time.time())
    log = scriptlog.objects.all()
    L = [i.sort_time for i in log]
    if L:
        now_log_time = max(L)
        L.remove(now_log_time)
        two_log_time = max(L)
        log_one = scriptlog.objects.get(sort_time=now_log_time)
        log_two = scriptlog.objects.get(sort_time=two_log_time)
        log_data = [log_one,log_two]

    if request.method == 'POST':
        user = request.user                        ##日志记录
        uuid = request.POST.get('command','')
        command = scriptrepo.objects.get(pk=uuid).command
        parameter = request.POST.get('parameter','')
        command = command + " " + parameter          ##记录到日志里的操作，也要给ansible的参数
        sort_time = now                             ##日志记录
        groupname = "script_group"
        inventory = script_inventory(uuid,groupname)      ##ansible的参数
        playbook = "/etc/ansible/script_deploy.yml"
        res = ansiblex_deploy(inventory,playbook,groupname,command)
        logdata = scriptlog(user=user,command=command,result=res,sort_time=sort_time)
        logdata.save()
        return HttpResponseRedirect('/success/')

    return render(request,'automation/script_deploy.html',locals())
