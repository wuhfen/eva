#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from .models import Iptables, oldsite_line 
from .forms import IptablesForm
# Create your views here.
from api.ansible_api import ansiblex
import datetime
import json
import urllib2
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from django.core.urlresolvers import reverse
from .tasks import do_ansible
from celery.result import AsyncResult


def error(request):
    return render(request,'allow_list/error.html')

def welcome(request):
    if 'user_name' in request.GET:
        return HttpResponse('Welcome!~'+request.GET['user_name'])
    else:
        return render(request,'allow_list/welcome.html',locals())


def poll_state(request):
    """ A view to report the progress to the user """
    if 'task_id' in request.GET and request.GET['task_id']:
        task_id = request.GET['task_id']
        task = AsyncResult(task_id)
        data = task.status
    else:
        data = 'No task_id in the request'


    json_data = json.dumps(data)
    return HttpResponse(json_data, content_type='application/json')


@permission_required('Allow_list.add_iptables', login_url='/allow/error/')
def iptables(request):
    ff = IptablesForm()
    fo_errors = []
    view_rules = Iptables.objects.filter(i_comment__contains="WEB_PORT_")
    if 'okk' in request.POST:
        ff = IptablesForm(request.POST)
        if ff.is_valid():
            ip = str(ff.cleaned_data.get('ipaddr'))
            comment = ff.cleaned_data.get('comment')
            remark = ff.cleaned_data.get('remark')
            if remark == u"only_new":
                host_group = u"新平台"
                chain = "INPUT"
            else:
                host_group = u"老平台"
                chain = "FORWARD"
            # else:
            #     host_group = u"全平台"
            #     chain = "INPUT"
            ip_api = "http://freeapi.ipip.net/%s" % ip
            req = urllib2.Request(ip_api)
            rel = urllib2.urlopen(req).read()
            result = rel.strip('[]').replace('\"','').split(',')
            # if ("中国" not in result) and ("香港" not in result):
            #     fo_errors.append("你输入的IP是:%s,IP属于:%s,添加状态：失败" % (ip,rel))
            if not fo_errors:
                comment = u"WEB_PORT_%s" % comment
                user = request.user
                i = Iptables(i_comment=comment,i_chain=chain,i_source_ip=ip,i_user=user,i_remark=remark,i_tag=host_group)
                i.save()
                task = "/etc/ansible/insertip.yml"
                job = do_ansible.delay(task,ip,remark,comment)
                task_id = job.id
    return render(request,'allow_list/iptables.html',locals())



@permission_required('Allow_list.change_iptables', login_url='/allow/error/')
def iptables_delete(request):
    ff = IptablesForm()
    search_rules = Iptables.objects.filter(i_comment__contains="WEB_PORT_")
    if request.method == 'POST':
        if "delete" in request.POST:
            ruls_id = str(request.POST['delete'])
            delete_ruls = Iptables.objects.get(id=ruls_id)
            ipaddr = delete_ruls.i_source_ip
            remark = delete_ruls.i_remark
            comm = delete_ruls.i_comment
            delete_ruls.delete()
            task = "/etc/ansible/deleteip.yml"
            ansiblex(task,str(ipaddr),remark,comm)
            infos = "IP: %s 已经成功解除绑定" % str(ipaddr)
            #return HttpResponse(choice)
            return HttpResponseRedirect('/allow/welcome/')
        elif "searchcomment" in request.POST:
            ff = IptablesForm(request.POST)
            comment = request.POST.get('comment')
            search_rules = Iptables.objects.filter(i_comment__contains="%s"% comment)
            return render(request,"allow_list/iptables_delete.html",locals())
        else:
            ip = request.POST.get('searchip')
            search_rules = Iptables.objects.filter(i_source_ip__contains="%s"% ip)
            return render(request,"allow_list/iptables_delete.html",locals())

    return render(request,"allow_list/iptables_delete.html",locals())





@permission_required('Allow_list.change_oldsite_line', login_url='/allow/error/')
def linechange(request):
    line_errors = []
    if "change" in request.POST:
        if "choiceline" not in request.POST:
            line_errors.append("你没有选择需要切换的线路！")
        elif "choiceagent" not in request.POST:
            line_errors.append("你没有选择客户！")
        else:
            choiceagent = request.POST['choiceagent']
            choiceline = request.POST['choiceline']
            oldsite_line.objects.filter(agent_name__contains=choiceagent).update(status=False)
            if choiceline == u"line_one":
                oldsite_line.objects.filter(agent_name__contains=choiceagent).filter(number=1).update(status=True)
            elif choiceline == u"line_two":
                oldsite_line.objects.filter(agent_name__contains=choiceagent).filter(number=2).update(status=True)
            elif choiceline == u"line_three":
                oldsite_line.objects.filter(agent_name__contains=choiceagent).filter(number=3).update(status=True)
            elif choiceline == u"line_four":
                oldsite_line.objects.filter(agent_name__contains=choiceagent).filter(number=4).update(status=True)
            
            task = "/etc/ansible/changeline.yml"
            ansiblex(task,choiceagent,choiceline)

            return HttpResponseRedirect('/allow/welcome/')
        return render(request,"allow_list/linechange.html",locals())
    elif "search" in request.POST:
        if "choiceagent" not in request.POST:
            line_errors.append("你没有选择客户！")
        else:
            choiceagent = request.POST['choiceagent']
            search_lines = oldsite_line.objects.filter(agent_name__contains=choiceagent)
        return render(request,"allow_list/linechange.html",locals())
    else:
        return render(request,"allow_list/linechange.html",locals())
