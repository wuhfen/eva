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
from api.ssh_api import ssh_cmd
import time
from django.http import JsonResponse

@permission_required('automation.add_Tools', login_url='/auth_error/')
def add_script(request):
    sf = ScriptForm()
    msg = ""
    if request.method == 'POST':
        fabuname = request.POST.get('name')
        command = request.POST.get('command')
        server_ip = request.POST.get('server_ip')
        memo = request.POST.get('memo')
        ff = request.POST.get('custom_state')
        if ff:
            dd = request.POST.lists()
            bb = len(dd)-5
            args_dict = {}
            L = []
            if bb/2 is not 0:
                for i in range(bb/2):
                    name = request.POST.get('group_name'+str(i))
                    args = request.POST.get('group_args'+str(i))
                    if name and args:
                        args_list = [r for r in args.split('\r\n')]
                        L.append({name: args_list})
                    else:
                        msg = u"信息没有填写完整！"
            if not msg:
                data = scriptrepo(name=fabuname,command=command,server_ip=server_ip,memo=memo,customargs=L,custom_state=True)
                data.save()
            return HttpResponseRedirect('/deploy/script_list')
        else:
            data = scriptrepo(name=fabuname,command=command,server_ip=server_ip,memo=memo,custom_state=False)
            data.save()
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
    for i in data:
        print i.uuid
        print i.custom_state
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
        try:
            now_log_time = max(L)
            L.remove(now_log_time)
            two_log_time = max(L)
            L.remove(two_log_time)
            three_log_time = max(L)
        except:
            log_data = []
        else:
            log_one = scriptlog.objects.get(sort_time=now_log_time)
            log_two = scriptlog.objects.get(sort_time=two_log_time)
            log_three = scriptlog.objects.get(sort_time=three_log_time)
            log_data = [log_one,log_two,log_three]

    if request.method == 'POST':
        ll = request.POST.lists()
        num = len(ll) - 3
        args_list = []
        if num is not 0:
            for i in range(num):
                select_name = "select_script"+str(i)
                args = request.POST.get(select_name,'')
                args_list.append(args)

        customargs = " ".join(args_list)

        user = request.user                        ##日志记录
        uuid = request.POST.get('command','')
        command = scriptrepo.objects.get(pk=uuid).command
        host = scriptrepo.objects.get(pk=uuid).server_ip
        parameter = request.POST.get('parameter','')
        command = command + " " + customargs + " " + parameter          ##记录到日志里的操作，也要给ansible的参数
        print command
        # return HttpResponse(command)
        sort_time = now                             ##日志记录
        # groupname = "script_group"
        # inventory = script_inventory(uuid,groupname)      ##ansible的参数
        # playbook = "/etc/ansible/script_deploy.yml"
        # res = ansiblex_deploy(inventory,playbook,groupname,command)
        res = ssh_cmd(host,command)
        string = ""
        for i in res:
            string = string+i

        # res = [i.decode('utf-8') for i in res]
        logdata = scriptlog(user=user,command=command,result=string,sort_time=sort_time)
        logdata.save()
        return HttpResponseRedirect('/success/')

    return render(request,'automation/script_deploy.html',locals())

def script_select(request):
    uuid = request.GET.get('uuid',0)
    data = scriptrepo.objects.get(pk=uuid)
    L = []
    if data.custom_state:
        customargs = eval(data.customargs)
        num = len(customargs)
        for i in range(num):
            select_name = "select_script"+str(i)
            for k,v in customargs[i].items():
                select_lab = "参数组："+ k
                option_val = v
                json_data = {
                    'select_name': select_name,
                    'select_lab': select_lab,
                    'option_val': option_val
                }
                L.append(json_data)

        # print L
    return JsonResponse(L,safe=False)

def script_memo(request):
    uuid = request.GET.get('uuid',0)
    print uuid
    obj = scriptrepo.objects.get(pk=uuid)
    print obj.memo
    data = {'res': obj.memo}
    print data
    return JsonResponse(data,safe=False)

def script_log_list(request):
    data = scriptlog.objects.all()
    return render(request,'automation/script_log_list.html',locals())