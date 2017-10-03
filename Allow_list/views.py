#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import Iptables,oldsite_line
from .forms import IptablesForm
# Create your views here.
from api.ansible_api import ansiblex
import time
import json
import urllib2,urllib
from business.models import Business
from .tasks import do_ansible,change_backend_task,change_backend_second
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
    data = [i.i_source_ip for i in Iptables.objects.all()]
    choice_data = [a for a in Business.objects.filter(nic_name__contains='10')]
    if 'okk' in request.POST:
        ip = request.POST.get('ipaddr')
        comment = request.POST.get('customer')
        remark = "only_new"
        host_group = u"新平台"
        chain = "INPUT"
        comment = u"WEB_PORT_%s" % comment
        user = request.user
        if ip in data:
            fo_errors.append("你输入的VPN_IP: %s 已存在,添加失败!" % ip) 
        # ip_api = "http://freeapi.ipip.net/%s" % ip
        # req = urllib2.Request(ip_api)
        # rel = urllib2.urlopen(req).read()
        # result = rel.strip('[]').replace('\"','').split(',')
        # if ("中国" not in result) and ("香港" not in result):
        #     fo_errors.append("你输入的IP是:%s,IP属于:%s,添加状态：失败" % (ip,rel))
        if not fo_errors:
            i = Iptables(i_comment=comment,i_chain=chain,i_source_ip=ip,i_user=user,i_remark=remark,i_tag=host_group)
            i.save()
            task = "/etc/ansible/insertip.yml"
            job = do_ansible.delay(task,ip,remark,comment)
            task_id = job.id
    return render(request,'allow_list/iptables.html',locals())


@permission_required('Allow_list.change_iptables', login_url='/allow/error/')
def iptables_delete(request,id):
    data = Iptables.objects.get(pk=id)
    ipaddr = data.i_source_ip
    remark = data.i_remark
    comm = data.i_comment
    count_num = Iptables.objects.filter(i_source_ip=ipaddr)
    if len(count_num) > 1:
        data.delete()
        infos = "IP: %s 已经成功解除绑定" % str(ipaddr)
        return JsonResponse({'res':"OK",'info':infos},safe=False)
    data.delete()
    task = "/etc/ansible/deleteip.yml"
    ansiblex(task,str(ipaddr),remark,comm)
    infos = "IP: %s 已经成功解除绑定" % str(ipaddr)
    return JsonResponse({'res':"OK",'info':infos},safe=False)

def iptables_search(request,comment):
    data = ["<p>"+i.i_source_ip+"</p>" for i in Iptables.objects.filter(i_comment=comment)]
    data = "".join(data)
    print data
    return JsonResponse({'res':data},safe=False)

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

def backend_status(request):
    siteid_data = Business.objects.filter(nic_name__contains="10").order_by('nic_name')
    data = oldsite_line.objects.get(agent='备用后台')
    if request.method == 'POST':
        siteid = request.POST.get('siteid')
        b_data = Business.objects.get(nic_name=siteid)
        if b_data.reserve_b:
            print "生效中转为未启用"
            b_data.reserve_b = False
            change_backend_second.delay(data.host_ip,siteid,False)
            res = {"res":"OK","info":"后台节点已停用"}
        else:
            print "未启用转为生效中"
            b_data.reserve_b = True
            change_backend_second.delay(data.host_ip,siteid,True)
            res = {"res":"OK","info":"后台节点已启用"}
        b_data.save()
        
        return JsonResponse(res,safe=False)
    return render(request,'allow_list/backend_status.html',locals())

def change_backend(request,id):
    data = oldsite_line.objects.get(pk=id)
    print data.status
    if data.status:
        res = {"res":"OK","info":"后台节点已停用"}
        data.status = False
        include_name = "status"
    else:
        res = {"res":"OK","info":"后台节点已启用"}
        data.status = True
        include_name = "*"
    data.save()
    a = change_backend_task.delay(data.host_ip,include_name)
    print a.result
    return JsonResponse(res,safe=False)




# 给客服用的管理域名的界面catg
def kefu_domain_list(request):
    return render(request,'allow_list/domain_list.html',locals())