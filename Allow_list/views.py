#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import Iptables,oldsite_line,white_conf,white_list
from .forms import IptablesForm,WhiteConfForm
# Create your views here.
from api.ansible_api import ansiblex
import time
import json
# import urllib2,urllib

from .tasks import do_ansible,change_backend_task,change_backend_second
from celery.result import AsyncResult
from business.models import Business
from business.tasks import dns_resolver_ip
from automation.models import gengxin_code
from automation.tasks import fabu_nginxconf_task

from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from api.paginator_api import JuncheePaginator
from api.common_api import isValidIp

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

def iptables_list(request):
    try:  
        page = int(request.GET.get("page",1))
        print request.GET
        print('page----->',page)
        if page < 1:  
            page = 1  
    except ValueError:  
        page = 1
    data = Iptables.objects.all().order_by('i_comment')
    paginator = JuncheePaginator(data, 10)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    return render(request,'allow_list/iptables_list.html',locals())


@permission_required('Allow_list.add_iptables', login_url='/allow/error/')
def iptables(request):
    choice_data = [a for a in Business.objects.filter(platform='现金网')]
    if request.method == 'POST':
        ip = request.POST.get('ipaddr').strip()
        comment = request.POST.get('customer').strip()
        remark = "only_new"
        host_group = u"新平台"
        chain = "INPUT"
        comment = u"WEB_PORT_%s" % comment
        user = request.user
        if not isValidIp(ip): return JsonResponse({"res": "falid","info": "IP格式错误"},safe=False)
        if Iptables.objects.filter(i_source_ip=ip): return JsonResponse({"res": "falid","info": "此IP已存在"},safe=False)

        i = Iptables(i_comment=comment,i_chain=chain,i_source_ip=ip,i_user=user,i_remark=remark,i_tag=host_group)
        i.save()
        task = "/etc/ansible/insertip.yml"
        job = do_ansible.delay(task,ip,remark,comment)
        task_id = job.id
        return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)
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
        infos = "IP: %s Deleted! " % str(ipaddr)
        return JsonResponse({'res':"OK",'info':infos},safe=False)
    data.delete()
    task = "/etc/ansible/deleteip.yml"
    ansiblex(task,str(ipaddr),remark,comm)
    infos = "IP: %s Deleted!" % str(ipaddr)
    return JsonResponse({'res':"OK",'info':infos},safe=False)

def iptables_search(request):
    comment = request.GET.get('comment','')
    print comment
    result = {}
    ip_res = [i for i in Iptables.objects.filter(i_source_ip__contains=comment)]
    comment_res = [i for i in Iptables.objects.filter(i_comment__contains=comment)]
    res = list(set(ip_res).union(set(comment_res)))
    if res:
        fff = []
        for i in res:
            print i.i_date_time
            fff.append({"ip":i.i_source_ip,"comment":i.i_comment,"date":i.i_date_time.strftime('%Y-%m-%d %H:%M:%S'),"user":i.i_user.first_name,"uuid":i.id})
        result["res"] = "OK"
        result["info"] = fff
    else:
        result["res"] = "Faild"

    return JsonResponse(result,safe=False)

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




# nginx白名单配置管理函数
def white_conf_list(request):
    data = white_conf.objects.all()
    return render(request,'allow_list/white_conf_list.html',locals())

def white_conf_modify(request,uuid):
    data = white_conf.objects.get(pk=uuid)
    wform = WhiteConfForm(instance=data)
    if request.method == 'POST':
        wform = WhiteConfForm(request.POST,instance=data)
        if wform.is_valid():
            wform.save()
        return JsonResponse({"res":"OK"},safe=False)
    return render(request,'allow_list/white_conf_modify.html',locals())

def white_list(request):
    data = white_list.objects.all()
    return render(request,'allow_list/white_list.html',locals())
