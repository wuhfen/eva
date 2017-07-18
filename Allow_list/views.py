#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from .models import Iptables, oldsite_line 
from .forms import IptablesForm
# Create your views here.
from api.ansible_api import ansiblex
import time
import json
import urllib2,urllib

from .tasks import do_ansible
from celery.result import AsyncResult
from business.models import Business
from business.tasks import dns_resolver_ip
from automation.models import gengxin_code
from automation.tasks import fabu_nginxconf_task
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
            comment = ff.cleaned_data.get('customer')
            remark = ff.cleaned_data.get('background')
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

            count_num = Iptables.objects.filter(i_source_ip=ruls_id)
            if len(count_num) > 1:
                delete_ruls.delete()
                infos = "IP: %s 已经成功解除绑定" % str(ipaddr)
                return HttpResponseRedirect('/allow/welcome/')

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



def changes(a,b):
   for i in xrange(0,len(a),b):
       yield  a[i:i+b]

@permission_required('Allow_list.change_oldsite_line', login_url='/allow/error/')
def linechange(request):
    data = Business.objects.filter(nic_name__contains="10").order_by('nic_name')
    user = request.user

    rules = []
    for i in changes(data,7):
        rules.append(i)
    try:
        rules0 = rules[0]
    except:
        rules0 = []
    try:
        rules1 = rules[1]
    except:
        rules1 = []
    try:
        rules2 = rules[2]
    except:
        rules2 = []


    return render(request,"allow_list/linechange.html",locals())



def pull_data(request,choice):
    """用户提交版本发布信息"""

    data = Business.objects.get(pk=choice)
    if data.reserve_a:
        iplist = dns_resolver_ip(data.reserve_a)
        if not iplist:
            iplist = ['Nothing']
        Business.objects.filter(pk=choice).update(front_station=iplist)
    if request.method == 'POST':
        domainname = request.POST.get('monitor_url')
        if domainname:
            data = Business.objects.filter(pk=choice).update(reserve_a=domainname)
            return HttpResponseRedirect('/allow/linechange/')
    return render(request,'allow_list/pull_data.html',locals())

def push_data(request,choice):
    """修改域名"""
    select = choice.split('_')[0]
    uuid = choice.split('_')[1]
    business = Business.objects.get(pk=uuid)
    try:
        data = gengxin_code.objects.filter(classify="online").get(business=business)
        if select == "web":
            print "修改web域名"
            domainname = data.front_domain
        elif select == "ag":
            print "修改代理后台域名"
            domainname = data.agent_domain
        else:
            print "修改ds168后台域名"
            domainname = data.backend_domain
    except:
        data = None

    if request.method == 'POST':
        domain = request.POST.get('domain')
        print domain
        if "web_" in choice:
            data.front_domain = domain
            classify = "front"
        elif "ag_" in choice:
            data.agent_domain = domain
            classify = "agent"
        else:
            classify = "backend"
            data.backend_domain = domain 
        data.save()
        print data.phone_site
        configurate = fabu_nginxconf_task.delay(data.uuid,choice=classify)
    return render(request,'allow_list/push_data.html',locals())