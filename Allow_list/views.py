#!/usr/bin/env python
# coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect,JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import Iptables,oldsite_line,white_conf,white_list
from gitfabu.models import git_deploy
from assets.models import Server

from .forms import WhiteConfForm
# Create your views here.
from api.ansible_api import ansiblex
import time
import json
# import urllib2,urllib

from .tasks import do_ansible,change_backend_task,change_backend_second,nginx_white_copy
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
    u"""操作成功，返回首页or上一页"""
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
    """现金网备用后台"""
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


# nginx黑名单（现金网和蛮牛）
def black_list_fun(request):
    try:  
        page = int(request.GET.get("page",1))
        print request.GET
        print('page----->',page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    data = white_list.objects.filter(host_key="deny")
    paginator = JuncheePaginator(data, 15)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)
    return render(request,'allow_list/black_list.html',locals())

def black_add(request):

    if request.method == 'POST':
        ip = request.POST.get('ipaddr').strip()
        if not isValidIp(ip): return JsonResponse({"res": "falid","info": "IP格式错误"},safe=False)
        classify = request.POST.get('classify')
        conf = white_conf.objects.get(name=classify)
        if not conf.servers: return JsonResponse({"res": "falid","info": "项目没有配置服务器"},safe=False)
        for i in conf.servers.split('\r\n'):
            if Server.objects.filter(ssh_host=i).count() != 1: return JsonResponse({"res": "falid","info": "请检查CMDB中服务器配置是否正确！"},safe=False)
        obj,created = white_list.objects.get_or_create(host_ip=ip,white_conf=conf,defaults={'host_key':"deny",'user':request.user})
        if not created: return JsonResponse({"res": "falid","info": "此IP已存在黑名单中"},safe=False)
        if white_list.objects.filter(white_conf=conf,host_ip=ip).count() > 1: return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)

        if classify == "MONEY-Black":
            template_file="kg_jdc_white.conf"
            ips = ""
            for i in white_list.objects.filter(white_conf=conf):
                ips += i.host_key+" "+i.host_ip+";\n"
            nginx_white_copy.delay(conf.servers,template_file,conf.file_path,ips,conf.is_reload)
        return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)

    return render(request,'allow_list/black_add.html',locals())

# NGINX 白名单 函数
def white_list_fun(request,which):
    try:
        page = int(request.GET.get("page",1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    try:
        conf = white_conf.objects.get(name=which)
        uuid = conf.id
        data = white_list.objects.filter(white_conf=conf)
    except:
        return HttpResponse("你还没有配置白名单服务器！")
    paginator = JuncheePaginator(data, 15)
    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)
    return render(request,'allow_list/white_list.html',locals())

def white_vip(request,uuid):
    #特权vip,没有添加次数限制
    conf = white_conf.objects.get(pk=uuid)

    if request.method == 'POST':
        vips = request.POST.get('ipaddr')
        conf.exception_ip = vips
        conf.save()
        return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)
    return render(request,'allow_list/white_vip.html',locals())


def white_batch_add(request,uuid):
    conf = white_conf.objects.get(pk=uuid)
    if conf.name == "KG-JDC" or conf.name == "MONEY-Backend" or conf.name == "DT-GFC" or conf.name == "MONEY-Black":
        data = git_deploy.objects.filter(platform="现金网",classify="online",isops=True,islog=True) #根据线上的siteid来添加
    elif conf.name == "MN-JDC" or conf.name == "MN-Backend" or conf.name == "MN-GFC" or conf.name == "MN-Black":
        data = git_deploy.objects.filter(platform="蛮牛",classify="huidu",isops=True,islog=True) #根据灰度的siteid来添加
    else:
        data = git_deploy.objects.filter(classify="online",islog=True)
    if request.method == 'POST':
        ips = request.POST.get('ipaddr').strip()
        method = request.POST.get('method').strip()
        classify = conf.name
        uuid = request.POST.get('uuid')
        deploy = git_deploy.objects.get(id=uuid)
        if conf.exception_ip: 
            exception = conf.exception_ip
        else:
            exception = ""
        if not conf.servers: return JsonResponse({"res": "falid","info": "项目没有配置服务器"},safe=False)
        for i in conf.servers.split('\r\n'):
            if Server.objects.filter(ssh_host=i).count() != 1: return JsonResponse({"res": "falid","info": "请检查CMDB中服务器配置是否正确！"},safe=False)

        for ip in ips.split('\r\n'):
            if not isValidIp(ip): return JsonResponse({"res": "falid","info": "IP格式错误: %s"% ip},safe=False)
            if ip not in exception:
                if white_list.objects.filter(white_conf=conf,host_ip=ip).count() >= 5: return JsonResponse({"res": "falid","info": "此IP: %s已绑定超过5个网站"% ip},safe=False)
        for ip in ips.split('\r\n'):
            obj,created = white_list.objects.get_or_create(host_ip=ip,git_deploy=deploy,white_conf=conf,defaults={'host_key':method,'user':request.user})
        ips = ""
        if classify == "KG-JDC" or classify == "MN-JDC" or classify == "DT-GFC" or classify == "MN-GFC":
            template_file="kg_jdc_white.conf"
            for i in white_list.objects.filter(white_conf=conf):
                ips += i.host_key+" "+i.host_ip+"; #"+i.git_deploy.name+" \n"
            print "添加%s"% classify
            job = nginx_white_copy.delay(conf.servers,template_file,conf.file_path,ips,conf.is_reload)
        elif classify == "MN-Backend" or classify == "MN-Black":
            platform = "蛮牛"
            template_file="mn_backend.conf"
            file_path = conf.file_path+"/"+deploy.name+".conf"
            huidu_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="huidu",isops=True,islog=True)
            online_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="online",isops=True,islog=True)
            if huidu_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=huidu_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            #print "找到灰度后台白名单：\n%s"% ips
            if online_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            #print "所有后台白名单：\n%s"% ips
            business = Business.objects.get(nic_name=deploy.name,platform=platform) #蛮牛项目
            front_data = business.domain.filter(use=2,classify="online") #蛮牛线上在用的后台域名对象
            if not front_data:
                front_data = business.domain.filter(use=2,classify="huidu")
            front_domain = " ".join([i.name for i in front_data if i]) #提取域名组成列表
            job = nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload,server_name=front_domain,siteid=deploy.name)
        else:
            platform = "现金网" #现金网后台反代节点nginx配置文件不统一,没法做文件模板覆盖
            template_file="kg_jdc_white.conf"
            file_path = conf.file_path+"/"+deploy.name+"_white_list"
            online_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="online",isops=True,islog=True)
            for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                ips += i.host_key+" "+i.host_ip+";\n"
            print "所有现金网后台白名单：\n%s"% ips
            job = nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload)
        return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)
    return render(request,'allow_list/white_batch_add.html',locals())

def white_add(request,uuid):
    conf = white_conf.objects.get(pk=uuid)
    if conf.name == "KG-JDC" or conf.name == "MONEY-Backend" or conf.name == "DT-GFC" or conf.name == "MONEY-Black":
        data = git_deploy.objects.filter(platform="现金网",classify="online",isops=True,islog=True) #根据线上的siteid来添加
    elif conf.name == "MN-JDC" or conf.name == "MN-Backend" or conf.name == "MN-GFC" or conf.name == "MN-Black":
        data = git_deploy.objects.filter(platform="蛮牛",classify="huidu",isops=True,islog=True) #根据灰度的siteid来添加
    else:
        data = git_deploy.objects.filter(classify="online",islog=True)
    if request.method == 'POST':
        ip = request.POST.get('ipaddr').strip()
        method = request.POST.get('method').strip()
        classify = conf.name
        uuid = request.POST.get('uuid')
        deploy = git_deploy.objects.get(id=uuid)
        if conf.exception_ip: 
            exception = conf.exception_ip
        else:
            exception = ""
        if not isValidIp(ip): return JsonResponse({"res": "falid","info": "IP格式错误"},safe=False)
        if not conf.servers: return JsonResponse({"res": "falid","info": "项目没有配置服务器"},safe=False)
        for i in conf.servers.split('\r\n'):
            if Server.objects.filter(ssh_host=i).count() != 1: return JsonResponse({"res": "falid","info": "请检查CMDB中服务器配置是否正确！"},safe=False)
        #判断该IP是否添加了5次,如果是特赦IP则不进行判断
        if ip not in exception:
            if white_list.objects.filter(white_conf=conf,host_ip=ip).count() >= 5: return JsonResponse({"res": "falid","info": "此IP已绑定超过5个网站"},safe=False)

        obj,created = white_list.objects.get_or_create(host_ip=ip,git_deploy=deploy,white_conf=conf,defaults={'host_key':method,'user':request.user})
        if not created: return JsonResponse({"res": "falid","info": "此项目的IP已存在"},safe=False)
        if white_list.objects.filter(white_conf=conf,git_deploy=deploy,host_ip=ip).count() > 1: return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)
        ips = ""
        if classify == "KG-JDC" or classify == "MN-JDC" or classify == "DT-GFC" or classify == "MN-GFC":
            template_file="kg_jdc_white.conf"
            for i in white_list.objects.filter(white_conf=conf):
                ips += i.host_key+" "+i.host_ip+"; #"+i.git_deploy.name+" \n"
            print "添加%s"% classify
            job = nginx_white_copy.delay(conf.servers,template_file,conf.file_path,ips,conf.is_reload)
        elif classify == "MN-Backend" or classify == "MN-Black":
            platform = "蛮牛"
            template_file="mn_backend.conf"
            file_path = conf.file_path+"/"+deploy.name+".conf"
            huidu_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="huidu",isops=True,islog=True)
            online_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="online",isops=True,islog=True)
            if huidu_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=huidu_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            #print "找到灰度后台白名单：\n%s"% ips
            if online_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            #print "所有后台白名单：\n%s"% ips
            business = Business.objects.get(nic_name=deploy.name,platform=platform) #蛮牛项目
            front_data = business.domain.filter(use=2,classify="online") #蛮牛线上在用的后台域名对象
            if not front_data:
                front_data = business.domain.filter(use=2,classify="huidu")
            front_domain = " ".join([i.name for i in front_data if i]) #提取域名组成列表
            job = nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload,server_name=front_domain,siteid=deploy.name)
        else:
            platform = "现金网" #现金网后台反代节点nginx配置文件不统一,没法做文件模板覆盖
            template_file="kg_jdc_white.conf"
            file_path = conf.file_path+"/"+deploy.name+"_white_list"
            online_deploy = git_deploy.objects.filter(platform=platform,name=deploy.name,classify="online",isops=True,islog=True)
            for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                ips += i.host_key+" "+i.host_ip+";\n"
            print "所有现金网后台白名单：\n%s"% ips
            job = nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload) #将白名单推到后台反代节点1001_white_list
        return JsonResponse({"res": "OK","info": "已添加成功"},safe=False)
    return render(request,'allow_list/white_add.html',locals())

def white_delete(request,uuid):
    data = white_list.objects.get(pk=uuid)
    ipaddr = data.host_ip
    deploy = data.git_deploy
    name = data.white_conf.name
    conf = white_conf.objects.get(name=name)
    print name

    if white_list.objects.filter(host_ip=ipaddr,git_deploy=deploy,white_conf=conf).count() > 1:
        print "找到多条,删除一条"
        data.delete()
        return HttpResponseRedirect('/allow/welcome/')

    data.delete()
    ips = ""
    if name == "KG-JDC" or name == "MN-JDC" or name == "DT-GFC" or name == "MN-GFC":
        template_file="kg_jdc_white.conf"
        for i in white_list.objects.filter(white_conf=conf):
            ips += i.host_key+" "+i.host_ip+"; #"+i.git_deploy.name+" \n"
        nginx_white_copy.delay(conf.servers,template_file,conf.file_path,ips,conf.is_reload)
    elif name == "MONEY-Black" or name == "MONEY-Backend":
        template_file="kg_jdc_white.conf"
        file_path = conf.file_path+"/"+deploy.name+"_white_list"
        for i in white_list.objects.filter(white_conf=conf,git_deploy=deploy):
            ips += i.host_key+" "+i.host_ip+";\n"
        nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload) #重新同步配置文件
    elif name == "MN-Backend":
        template_file="mn_backend.conf"
        file_path = conf.file_path+"/"+deploy.name+".conf"
        huidu_deploy = git_deploy.objects.filter(platform="蛮牛",name=deploy.name,classify="huidu",isops=True,islog=True)
        online_deploy = git_deploy.objects.filter(platform="蛮牛",name=deploy.name,classify="online",isops=True,islog=True)

        if huidu_deploy:
            for i in white_list.objects.filter(white_conf=conf,git_deploy=huidu_deploy[0]):
                ips += i.host_key+" "+i.host_ip+";\n    "
                print "找到灰度后台白名单：%s"% ips
        if online_deploy:
            for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                ips += i.host_key+" "+i.host_ip+";\n    "
        print "所有后台白名单：%s"% ips
        business = Business.objects.get(nic_name=deploy.name,platform=u"蛮牛") #蛮牛项目
        front_data = business.domain.filter(use=2,classify="online") #蛮牛线上在用的后台域名对象
        if not front_data:
                front_data = business.domain.filter(use=2,classify="huidu")
        front_domain = " ".join([i.name for i in front_data if i]) #提取域名组成列表
        nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload,server_name=front_domain,siteid=deploy.name)
    return HttpResponseRedirect('/allow/welcome/')

def batch_delete_vpn(request):
    vpns = request.GET.get('vpns')
    name = request.GET.get('project')
    conf = white_conf.objects.get(name=name)
    id_list = vpns.split(",")
    ips = ""
    if name == "KG-JDC" or name == "MN-JDC" or name == "DT-GFC" or name == "MN-GFC":
        template_file="kg_jdc_white.conf"
        for i in id_list:
            if i:
                data = white_list.objects.get(pk=i)
                data.delete()
        for i in white_list.objects.filter(white_conf=conf):
            ips += i.host_key+" "+i.host_ip+"; #"+i.git_deploy.name+" \n"
        nginx_white_copy.delay(conf.servers,template_file,conf.file_path,ips,conf.is_reload)
    elif name == "MONEY-Black" or name == "MONEY-Backend":
        template_file="kg_jdc_white.conf"
        deploys = []
        for i in id_list:
            if i:
                data = white_list.objects.get(pk=i)
                deploy = data.git_deploy
                deploys.append(deploy)
                data.delete()
        new_deploys = list(set(deploys))
        if len(new_deploys) == 1:
            file_path = conf.file_path+"/"+deploy.name+"_white_list"
            for i in white_list.objects.filter(white_conf=conf,git_deploy=deploy):
                ips += i.host_key+" "+i.host_ip+";\n"
            nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload) #重新同步配置文件
        else:
            for i in new_deploys:
                file_path = conf.file_path+"/"+i.name+"_white_list"
                ips = ""
                for j in white_list.objects.filter(white_conf=conf,git_deploy=i):
                    ips += j.host_key+" "+j.host_ip+";\n"
                nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload) 
    elif name == "MN-Backend":
        template_file="mn_backend.conf"
        deploys = []
        for i in id_list:
            if i:
                data = white_list.objects.get(pk=i)
                deploy = data.git_deploy
                deploys.append(deploy)
                data.delete()
        new_deploys = list(set(deploys))
        if len(new_deploys) == 1:
            file_path = conf.file_path+"/"+deploy.name+".conf"
            huidu_deploy = git_deploy.objects.filter(platform="蛮牛",name=deploy.name,classify="huidu",isops=True,islog=True)
            online_deploy = git_deploy.objects.filter(platform="蛮牛",name=deploy.name,classify="online",isops=True,islog=True)
            if huidu_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=huidu_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            if online_deploy:
                for i in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                    ips += i.host_key+" "+i.host_ip+";\n    "
            business = Business.objects.get(nic_name=deploy.name,platform=u"蛮牛") #蛮牛项目
            front_data = business.domain.filter(use=2,classify="online") #蛮牛线上在用的后台域名对象
            if not front_data: front_data = business.domain.filter(use=2,classify="huidu")
            front_domain = " ".join([i.name for i in front_data if i]) #提取域名组成列表
            nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload,server_name=front_domain,siteid=deploy.name)
        else:
            for i in new_deploys:
                ips = ""
                business = Business.objects.get(nic_name=i.name,platform=u"蛮牛")
                front_data = business.domain.filter(use=2,classify="online")
                if not front_data: front_data = business.domain.filter(use=2,classify="huidu")
                front_domain = " ".join([j.name for j in front_data if j])
                file_path = conf.file_path+"/"+i.name+".conf"
                huidu_deploy = git_deploy.objects.filter(platform="蛮牛",name=i.name,classify="huidu",isops=True,islog=True)
                online_deploy = git_deploy.objects.filter(platform="蛮牛",name=i.name,classify="online",isops=True,islog=True)
                if huidu_deploy:
                    for j in white_list.objects.filter(white_conf=conf,git_deploy=huidu_deploy[0]):
                        ips += j.host_key+" "+j.host_ip+";\n    "
                if online_deploy:
                    for j in white_list.objects.filter(white_conf=conf,git_deploy=online_deploy[0]):
                        ips += j.host_key+" "+j.host_ip+";\n    "
                nginx_white_copy.delay(conf.servers,template_file,file_path,ips,conf.is_reload,server_name=front_domain,siteid=i.name)

    return JsonResponse({"status":"OK","info":"批量删除已完成!"})

def white_list_search(request):
    comment = request.GET.get('comment','')
    uuid = request.GET.get('uuid','')
    conf = white_conf.objects.get(pk=uuid)
    print comment
    result = {}
    comment_res = []
    ip_res = [i for i in white_list.objects.filter(host_ip__contains=comment,white_conf=conf) if i]

    huidu_obj = git_deploy.objects.filter(name=comment,classify="huidu")
    if huidu_obj:
        for i in huidu_obj[0].white.filter(white_conf=conf):
            comment_res.append(i)

    online_obj = git_deploy.objects.filter(name=comment,classify="online")
    if online_obj:
        for i in online_obj[0].white.filter(white_conf=conf):
            comment_res.append(i)

    res = list(set(ip_res).union(set(comment_res)))
    if res:
        fff = []
        for i in res:
            if i.white_conf.name ==  "KG-JDC":
                classify = 'KG经典彩'
            elif i.white_conf.name == "MN-Backend":
                classify = '蛮牛后台'
            elif i.white_conf.name == "MN-JDC":
                classify = '蛮牛经典彩'
            elif i.white_conf.name == "MN-GFC":
                classify = '蛮牛官方彩'
            elif i.white_conf.name == "DT-GFC":
                classify = '鼎泰官方彩'
            else:
                classify = "现金网后台"
            fff.append({"classify":classify,"siteid":i.git_deploy.name,"ip":i.host_ip,"method":i.host_key,"user":i.user.first_name,"date":i.ctime.strftime('%Y-%m-%d %H:%M:%S'),"uuid":i.id})
        result["res"] = "OK"
        result["info"] = fff
    else:
        result["res"] = "Faild"

    return JsonResponse(result,safe=False)