#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.contrib.auth.decorators import login_required, permission_required
# from forms import BusinessForm
from models import Business,DomainName,Domain_ip_pool,DomainInfo,accelerated_server_manager
from forms import BusinessForm, DomainNameForm,IPpoolForm
from api.ansible_api import ansiblex_domain
from api.ssh_api import ssh_cmd
from api.common_api import isValidIp
from api.zabbix_api import zabbixtools
from Allow_list.models import Iptables
from assets.models import Server,Project,Asset,NIC
import time
import json
import re
from tempfile import NamedTemporaryFile
import os
import telegram
from .tasks import monitor_code,jiasu_init_task
from .platfapi import jiasu_conf_rsync

##业务增删查改

def business_list(request):
    business_data = Business.objects.all()
    return render(request,'business/business_list.html',locals())


def business_delete(request,uuid):
    data = Business.objects.get(pk=uuid)
    data.delete()
    business_data = Business.objects.all()
    return render(request,'business/business_list.html',locals())


def business_add(request):
    bf = BusinessForm()
    if request.method == 'POST':
        bf = BusinessForm(request.POST)
        nic_name = request.POST.get('nic_name')
        if Business.objects.filter(nic_name=nic_name):
            return HttpResponseRedirect('/allow/welcome/')
        if bf.is_valid():
            bf_data = bf.save()
            bf_data.full_name=bf_data.name
            bf_data.status='0'
            bf_data.save()
            siteid = bf_data.nic_name
            if "new" in siteid:
                siteid=siteid.replace("new","")
            #需要创建测试环境和灰度环境的域名,傻啊，都不分现金网和蛮牛吗？
            if bf_data.platform == "现金网":
                test_f = DomainName(name=siteid+".test.s1118.com",use=0,business=bf_data,classify="test",state=0,supplier="工程")
                test_f.save()
                huidu_f = DomainName(name=siteid+".s1119.com",use=0,business=bf_data,classify="huidu",state=0,supplier="运维")
                huidu_a = DomainName(name="ag"+siteid+".s1119.com",use=1,business=bf_data,classify="huidu",state=0,supplier="运维")
                huidu_a.save()
                huidu_f.save()
            elif bf_data.platform == "VUE蛮牛":
                huidu_f = DomainName(name=siteid.replace("vue","")+".kg-8.me",use=0,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a = DomainName(name="ag"+siteid+".kg-8.me",use=1,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a.save()
                huidu_f.save()
            return HttpResponseRedirect('/business/business_list/')
    return render(request,'business/business_add.html',locals())


def business_edit(request,uuid):
    business = get_object_or_404(Business, uuid=uuid)
    status = business.status
    bf = BusinessForm(instance=business)
    if request.method == 'POST':
        bf = BusinessForm(request.POST,instance=business)
        new_status = request.POST.get('status', '')
        if bf.is_valid():
            status_change_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            bf_data = bf.save(commit=False)
            if status == new_status:
                bf_data.save()
            else:
                bf_data.status_update_date = status_change_time
                bf_data.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'business/business_edit.html',locals())


def business_detail(request,uuid):
    business_data = get_object_or_404(Business, uuid=uuid)
    front_ip = business_data.front_station
    front_proxy_ip = business_data.front_proxy
    backend_ip = business_data.backend_station
    backend_proxy_ip = business_data.backend_proxy
    ag_ip = business_data.third_party_node
    try:
        front_ip = front_ip.replace('\r\n'," ")
        front_proxy_ip = front_proxy_ip.replace('\r\n'," ")
        backend_ip = backend_ip.replace('\r\n'," ")
        backend_proxy_ip = backend_proxy_ip.replace('\r\n'," ")
        ag_ip = ag_ip.replace('\r\n'," ")
    except AttributeError:
        pass

    return render(request,'business/business_detail.html',locals())

##查看项目的各种配置文件
def business_conf_show(request):
    #1.获取ip，路径，文件
    ips = request.GET.get('ip')
    print ips.split(" ")
    path = request.GET.get('path')
    file = request.GET.get('file')
    tmp_file = "/tmp/tmp_nginx.conf"

    if str(path[-1]) is not "/":
        path =path+"/"+file
        path = "cat %s"% path
    else:
        path =path+file
        path = "cat %s"% path
    # print path
    f = open(tmp_file,"wb")
    for ip in ips.split(" "):
        ip_title = "##########%s %s##########\r\n"% (ip,path)
        f.write(ip_title)
        res = ssh_cmd(ip,str(path))
        for i in res:
            f.write(i)
    f.close()
    # print type(res)
    data = {'ip':ips}
    # return HttpResponse(res)
    return JsonResponse(data,safe=False)

from django.http import StreamingHttpResponse

def deploy_nginx_tmp_file(request):
    content = open('/tmp/tmp_nginx.conf', 'r').read()
    response = StreamingHttpResponse(content)
    response['Content-Type'] = 'text/plain; charset=utf8'
    return response



##IP池add delete search change
@permission_required('business.add_domainname', login_url='/auth_error/')
def domain_ip_list(request):
    ippool_data =  Domain_ip_pool.objects.all()
    return render(request,'business/domain_ip_list.html',locals())

@permission_required('business.add_domainname', login_url='/auth_error/')
def domain_ip_add(request):
    df = IPpoolForm()
    if request.method == 'POST':
        df = IPpoolForm(request.POST)
        if df.is_valid():
            df_data = df.save()
            return HttpResponseRedirect('/business/domain_ip_list/')
    return render(request,'business/domain_ip_add.html',locals())

@permission_required('business.add_domainname', login_url='/auth_error/')
def domain_ip_delete(request,uuid):
    domainname = get_object_or_404(Domain_ip_pool, uuid=uuid)
    domainname.delete()
    return render(request,'business/domain_ip_list.html',locals())

@permission_required('business.add_domainname', login_url='/auth_error/')
def domain_ip_edit(request,uuid):
    ippool_data = get_object_or_404(Domain_ip_pool, uuid=uuid)
    df = IPpoolForm(instance=ippool_data)
    if request.method == 'POST':
        df = IPpoolForm(request.POST,instance=ippool_data)
        if df.is_valid():
            df_data = df.save()
            return HttpResponseRedirect('/business/domain_ip_list/')
    return render(request,'business/domain_ip_edit.html',locals())


##改变域名监控状态

def change_domain_monitor_status(request):
    uuid = request.GET.get('uuid')
    # return HttpResponse(uuid)
    # status = request.GET.get('method')
    obj = DomainName.objects.get(pk=uuid)
    if obj.monitor_status:
        data = {'res':"yes"}
        domainname = DomainName.objects.filter(pk=uuid).update(monitor_status=False)
    else:
        data = {'res':"no"}
        domainname = DomainName.objects.filter(pk=uuid).update(monitor_status=True)
        # job = monitor_code.delay(60,uuid)
    return JsonResponse(data,safe=False)

def get_domain_status(request):
    # uuid = request.GET.get('uuid')
    # obj = DomainName.objects.get(pk=uuid)
    # name = obj.name
    # try:
    #     res_obj = DomainInfo.objects.filter(name=name,new_msg=True).first()
    #     if res_obj.alert == True:
    #         status = "red"
    #     else:
    #         status = "green"
    #     info = res_obj.info
    #     print info,"red-green"
    #     data = {'status':status,'info':info}
    # except AttributeError:
    data = {'status':'green','info':"NO INFOMATION"}
    return JsonResponse(data,safe=False)

def get_domain_code(request):
    uuid = request.GET.get('uuid')
    name = request.GET.get('name')
    axais = []
    yxais = []
    data = {'name':name,'axais':axais,'yxais':yxais}
    res_obj = DomainInfo.objects.filter(name=name)
    if res_obj:
        for i in res_obj:
            axais.append(i.created_at.replace(microsecond=0))
            yxais.append(i.res_code)
        data['xaxis'] = axais
        data['yaxis'] = yxais
    # print data
    return JsonResponse(data,safe=False)


def restart_all_monitor(request):
    ##由于重启celery后所有的在监控任务都失效，所以写一个一键让其任务重新进入celery的按钮
    data_list = DomainName.objects.all()
    maxnum = 60
    data = {'retu':"True"}
    return JsonResponse(data,safe=False)


##现金网和蛮牛的域名在线管理系统
def domain_list_select(request,siteid):
    business = Business.objects.get(pk=siteid)
    domain_data = DomainName.objects.filter(business=business)
    return render(request,'business/domain_list.html',locals())

def domain_add_select(request,siteid):
    business = Business.objects.get(pk=siteid)
    data = DomainName.objects.filter(business=business)
    errors = []
    if request.method == 'POST':
        use = request.POST.get('selectdomainuse')
        supplier = request.POST.get('selectdomainmanage')
        domainname = request.POST.get('description')
        classify = request.POST.get('selectclassify')
        if not use:
            errors.append("你没有选择域名用途！")
        if not supplier:
            errors.append("你没有选择域名管理者！")
        if not domainname:
            errors.append("你没有填写域名！")
        else:
            for i in domainname.split('\r\n'):
                if "." not in i.strip():
                    errors.append("你填写域名：%s 格式错误！"% i.strip())
                if use == '1' and "ag" not in i.strip():
                    errors.append("你填写域名：%s 格式错误！缺少ag"% i.strip())
                if use == '2' and "ds168" not in i.strip():
                    errors.append("你填写域名：%s 格式错误！缺少ds168"% i.strip())
                if use == '0' and ("ds168." in i.strip() or "ag." in i.strip()):
                    errors.append("网站域名：%s 不应该改包含ds168 or ag"% i.strip())
                if i.strip() in [x.name for x in DomainName.objects.filter(business=business,classify=classify,state='0',use=use)]:
                    errors.append("域名：%s 已存在"% i.strip())
        if errors:
            return JsonResponse({'res':"Failed","info":errors})
        # if use == '2':
        #     pool = Domain_ip_pool.objects.get(name="新站后台反代")
        # elif use == '1':
        #     pool = Domain_ip_pool.objects.get(name="新站第三方ag反代")
        # else:
        #     pool = Domain_ip_pool.objects.get(name="CDN（抗攻击）")
        for i in domainname.split('\r\n'):
            save_data = DomainName(name=i.strip(),use=use,business=business,state='0',classify=classify,supplier=supplier,monitor_status=False)
            save_data.save()
        return JsonResponse({'res':"OK"})
    return render(request,'business/domain_add_select.html',locals())



def domain_edit(request,uuid):
    domainname = get_object_or_404(DomainName, uuid=uuid)
    df = DomainNameForm(instance=domainname)
    business=domainname.business
    if request.method == 'POST':
        df = DomainNameForm(request.POST,instance=domainname)
        if df.is_valid():
            df_data = df.save()
            df_data.business=business
            df_data.save()
            return JsonResponse({'res':"OK"})
        else:
            return JsonResponse({'res':"Failed","info":"提交数据有错误!"})
    return render(request,'business/domain_edit.html',locals())


def domain_delete(request,uuid):
    domainname = get_object_or_404(DomainName, uuid=uuid)
    domainname.delete()
    return JsonResponse({'res':"OK",'info':"已删除！"},safe=False)
    # return render(request,'business/domain_list.html',locals())

import  xdrlib ,sys
import xlrd
from django.conf import settings
def domain_upload(request):
    if request.method == 'POST':
        file = request.FILES.get('docfile')
        basedir = settings.BASE_DIR + "/static/uploads/domain/"
        print basedir
        errors = []
        if not file:
            errors = ["你没有选择文件"]
            return render(request,'business/domain_import.html',locals())
        filename = os.path.join(basedir,file.name)
        fobj = open(filename,'wb')
        for chrunk in file.chunks():
            fobj.write(chrunk)
        fobj.close()
        data = xlrd.open_workbook(filename)
        table = data.sheets()[0]
        nrows = table.nrows #行数
        ncols = table.ncols #列数
        colnames =  table.row_values(0) #第一行标头数据 
        # print colnames
        if "siteid" not in colnames: errors.append("没有siteid列")
        if "域名" not in colnames: errors.append("没有域名列")
        if "类型" not in colnames: errors.append("没有域名类型列")
        if "管理者" not in colnames: errors.append("没有域名管理者列")
        if "备注" not in colnames: errors.append("没有域名备注列")
        if errors: return render(request,'business/domain_import.html',locals())

        list =[]
        for rownum in range(1,nrows):
            row = table.row_values(rownum)
            if row:
                app = {}
                app["Num"]=rownum
                for i in range(len(colnames)):
                    app[colnames[i]] = row[i]
                list.append(app)
        # print list

        for i in list:
            pps = []
            if not i[u"siteid"]: 
                pps.append("第%s行，没有给出siteid的值，跳过此行"% i["Num"])
                errors.append("第%s行，没有给出siteid的值，跳过此行"% i["Num"])
            if not i[u"域名"]: 
                pps.append("第%s行，没有给出域名，跳过此行"% i["Num"])
                errors.append("第%s行，没有给出域名，跳过此行"% i["Num"])
            elif "." not in i[u"域名"]:
                pps.append("第%s行，域名%s格式错误，跳过此行"% (i["Num"],i[u"域名"]))
                errors.append("第%s行，域名%s格式错误，跳过此行"% (i["Num"],i[u"域名"]))
            if not i[u"类型"]: 
                pps.append("第%s行，没有域名类型，跳过此行"% i["Num"])
                errors.append("第%s行，没有域名类型，跳过此行"% i["Num"])
            elif i[u"类型"] == u"前端域名":
                use = 0
            elif i[u"类型"] == u"后台域名":
                use = 2
            elif i[u"类型"] == u"代理后台域名":
                use = 1
            elif i[u"类型"] == u"导航域名":
                use = 3
            else:
                use = 4
            if not i[u"管理者"]: 
                pps.append("第%s行，没有给出管理员，跳过此行"% i["Num"])
                errors.append("第%s行，没有给出管理员，跳过此行"% i["Num"])
            if pps:
                continue  #跳过有错误的行
            else:
                print type(i[u"siteid"])
                if isinstance(i[u"siteid"],(float,int)):
                    nic_name = int(i[u"siteid"])
                else:
                    nic_name = str(i[u"siteid"])
                print nic_name

                try:
                    data = Business.objects.get(nic_name=nic_name)
                except:
                    errors.append("此站不存在：%s"% nic_name)
                    print "此站不存在：%s"% nic_name
                    continue
                try:
                    obj,created = DomainName.objects.get_or_create(name=i[u"域名"],defaults={'use':use,'business':data,'state':'1','supplier':i[u"管理者"],'description':i[u"备注"]})
                    if obj:
                        errors.append("此域名：%s已存在"% i[u"域名"])
                except:
                    print i[u"域名"]
                    errors.append("此域名：%s已存在多条，请保留一条！"% i[u"域名"])
        if errors: return render(request,'business/domain_import.html',locals())


    return render(request,'business/domain_import.html',locals())



def domain_detail(request,uuid):
    domain_data = get_object_or_404(DomainName, uuid=uuid)
    name = domain_data.name
    try:
        attribute = domain_data.address.attribute
        L = attribute.split('\r\n')
    except:
        L = []
    # print L
    res_obj = DomainInfo.objects.filter(name=name,new_msg=True).first()
    if res_obj:
        alert = res_obj.alert
        res_code = res_obj.res_code
        address = res_obj.address
        info = res_obj.info
        no_ip = res_obj.no_ip

    return render(request,'business/domain_detail.html',locals())



def domain_add_batch(request):
    """批量添加域名"""
    if request.method == 'POST':
        multi_domainname = request.POST.get('batch').split('\n')
        for domainname in multi_domainname:
            if domainname == '':
                break
            name,use,business = domainname.split()
            business = get_object_or_404(Business,name=business)
            if business:
                if use == u'前端域名':
                    use = '0'
                elif use == u'接口域名':
                    use = '1'
                elif use == u'后台域名':
                    use = '2'
                else:
                    emg = u'用途格式错误(前端域名|接口域名|后台域名)！'
                    return render(request,'business/domain_add_batch.html')
            else:
                emg = u'业务名称格式错误(新菲律宾|老菲律宾)！'
                return render(request,'business/domain_add_batch.html')

            domain_data = DomainName(name=name,use=use,business=business,state='0',status=True)
            domain_data.save()
        smg = u'批量添加成功.'
        return render(request,'business/domain_add_batch.html',locals())

    return render(request,'business/domain_add_batch.html',locals())

def domain_manage_business_list(request):
    data = Business.objects.filter(status=0)
    return render(request,'business/domain_manage_business_list.html',locals())


##将域名同步至服务器
# @permission_required('business.add_domainname', login_url='/auth_error/')
# def business_domain_rsync(request,uuid):
#     business = get_object_or_404(Business,uuid=uuid)
#     return render(request,'business/domain_rsync_to_server.html',locals())




# def get_inventory(tag,groupname):
#     hostsFile = NamedTemporaryFile(delete=False)
#     plat_data = Platform.objects.get(name=tag)
#     data = []
#     group = "[%s]" % groupname
#     data.append(group)
#     for i in plat_data.front_station.all():
#         hosts = "%s ansible_ssh_port=%s ansible_ssh_use=root ansible_ssh_pass=%s" % (i.ssh_host,i.ssh_port,i.ssh_password)
#         data.append(hosts)
#     for s in data:
#         hostsFile.write(s+'\n')
#     hostsFile.close()
#     return hostsFile.name



# def domain_rsync_to_server(request):
#     data = {}
#     data['group1'] = {'10.10.239.145':"root"}
#     if request.method == 'GET':
#         uuid = request.GET['uuid']
#         business = get_object_or_404(Business,uuid=uuid)
#         tag = business.platform.name
#         template_dir_one = business.platform.nic_name

#         use = request.GET['use']
#         domainname_list = [x.name for x in business.domainname_set.all() if x.use == use ]
#         domainname_list = ' '.join(domainname_list)
#         if use == '0':
#             groupname = 'front_station'
#             template_dir_two = 'front_station'
#             domainname_dir = business.front_station_web_dir
#             domainname_conf = business.front_station_web_file
#         elif use == '1' and tag == u"新平台":
#             groupname = 'third_party_node'
#             template_dir_two = 'third_proxy'
#             domainname_dir = business.third_proxy_web_dir
#             domainname_conf = business.third_proxy_web_file
#         elif use == '1' and tag == u"老平台":
#             groupname = 'front_station'
#             template_dir_two = 'front_station'
#             domainname_dir = business.front_station_web_dir
#             domainname_conf = business.front_station_web_file
#         else:
#             groupname = 'backend_proxy'
#             template_dir_two = 'backend_proxy'
#             domainname_dir = business.backend_station_web_dir
#             domainname_conf = business.backend_station_web_file

#         inventory = get_inventory(tag,groupname)
#         task = "/etc/ansible/domainname_rsync.yml"
#         ansiblex_domain(inventory,task,groupname,template_dir_one,template_dir_two,domainname_dir,domainname_conf,domainname_list)
#         print domainname_dir
#         print inventory
#         print domainname_list
#         os.remove(inventory)
#     return HttpResponse("SUCCESS")

def domain_monitor(request):
    pass


@login_required()
def acceleration_node_add(request):
    '''添加加速服务器,实现录入cmdb,实现添加入zabbix监控,实现初始化加速服务器功能'''
    if request.method == "POST":
        platfrom = request.POST.get('platfrom')
        name = request.POST.get('name')
        host1 = request.POST.get('ip1')
        host2 = request.POST.get('ip2')
        username = request.POST.get('user')
        port = request.POST.get('port')
        password = request.POST.get('password')
        stop_date = request.POST.get('stop_date')
        if not stop_date: stop_date = '2029-01-01'
        remark = request.POST.get('remark')
        if not remark: remark = "新增加速节点: %s ,IP1: %s IP2: %s"% (name,host1,host2)
        check_list = request.POST.getlist('checks')
        if accelerated_server_manager.objects.filter(name=name,online=True):return JsonResponse({'res':"Failed",'info':"名称已存在!"})
        if accelerated_server_manager.objects.filter(host_master=host1):return JsonResponse({'res':"Failed",'info':"IP1已存在!"})
        if accelerated_server_manager.objects.filter(host_slave=host2):return JsonResponse({'res':"Failed",'info':"IP2已存在!"})
        data = accelerated_server_manager(name=name,platfrom=platfrom,host_master=host1,host_slave=host2,username=request.user.username,stop_date=stop_date,remark=remark)
        data.save()
        if "add_cmdb" in check_list:
            print "CMDB添加服务器"
            if not Server.objects.filter(ssh_host=host1):
                jiasu_pro = Project.objects.get(project_name="加速服务器")
                Asset_obj = Asset(asset_type="virtual",purpose=name+"加速节点",remarks=remark)
                Asset_obj.save()
                Server_obj = Server(asset=Asset_obj,name=name,ssh_user=username,ssh_host=host1,ssh_port=port,ssh_password=password,Disk_total='200',RAM_total='8')
                Server_obj.save()
                Server_obj.project.add(jiasu_pro)
                NIC.objects.get_or_create(asset = Asset_obj,name="eth1",ipaddress=host2)
        if "init_jiasu" in check_list:
            print "初始化加速服务器"
            if 'send_msg' in check_list:
                reslut = jiasu_init_task.delay(host1,port,username,password,remark)
            else:
                reslut = jiasu_init_task.delay(host1,port,username,password)
        if 'zabbix' in  check_list:
            print "添加zabbix监控"
            zbx=zabbixtools("http://172.25.100.10/","zbxuser","zbxpass")
            if zbx.authID != 0:
                zbx.jiasu_host_create(host1,"%s-加速-%s"% (name,host1))
                zbx.jiasu_host_create(host2,"%s-加速-%s"% (name,host2))

        return JsonResponse({'res':"OK"},safe=False)
    return render(request,'business/acceleration_node_add.html',locals())

@login_required()
def acceleration_node_list(request):
    # data = accelerated_server_manager.objects.all()
    return render(request,'business/acceleration_node_list.html',locals())

@login_required()
def acceleration_nodes_get(request):
    """
    action: search 关键字搜素
    action: null 获取全部数据
    group: value 组搜索
    keyword: value 关键字搜索
    """
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    if page==1:
        start_line=0
        end_line=limit
    else:
        start_line=int(page)*int(limit)-int(limit)
        end_line=int(page)*int(limit)
    keyword = request.GET.get('keyword')
    group = request.GET.get('group')
    action = request.GET.get('action')
    list_data=[]
    if action == "search":
        if group!="all":
            if keyword:
                n_data = accelerated_server_manager.objects.filter(platfrom=group,name__contains=keyword)
                hma_data = accelerated_server_manager.objects.filter(platfrom=group,host_master__contains=keyword)
                hsa_data = accelerated_server_manager.objects.filter(platfrom=group,host_slave__contains=keyword)
                r_data = accelerated_server_manager.objects.filter(platfrom=group,remark__contains=keyword)
                data=list(set(n_data)|set(hma_data)|set(hsa_data)|set(r_data))[start_line:end_line]
            else:
                data=accelerated_server_manager.objects.filter(platfrom=group)[start_line:end_line]
        else:
            if keyword:
                n_data = accelerated_server_manager.objects.filter(name__contains=keyword)
                hma_data = accelerated_server_manager.objects.filter(host_master__contains=keyword)
                hsa_data = accelerated_server_manager.objects.filter(host_slave__contains=keyword)
                r_data = accelerated_server_manager.objects.filter(remark__contains=keyword)
                data=list(set(n_data)|set(hma_data)|set(hsa_data)|set(r_data))[start_line:end_line]
        count=len(data)
    else:
        data = accelerated_server_manager.objects.all()[start_line:end_line]
        count=accelerated_server_manager.objects.count()

    for i in data:
        list_data.append({'id':i.id,'group':i.platfrom,'name':i.name,'host_master':i.host_master,'host_slave':i.host_slave,'stop_date':i.stop_date,'online':i.online,'username':i.username,'ctime':i.create_date.strftime('%Y-%m-%d %H:%M:%S'),'remark':i.remark})
    res={'code':0,'msg':"加速服務器所有數據集",'count':count,'data':list_data}
    return JsonResponse(res)

@login_required()
def acceleration_api(request):
    """api参数
        id: 字段id
        value: 值
        action: change_status 修改字段online
        action: change_name 修改字段name
        action: change_group 修改字段platfrom
        action: change_date 修改字段stop_date
        action: change_remark 修改字段remark
        action: init 初始化 id为list
        action: zabbix 监控 id为list
        action: sync 同步 id为list
        返回
        code: 0成功1失败
        rid: 字段id
        msg: 信息
        data: 数据
        count: 数据统计
    """
    action=request.GET.get('action')
    field_id=request.GET.get('id')
    value=request.GET.get('value')
    result={"code":1,"rid":field_id,"msg":"Error"}
    if action=="change_status":
        data = accelerated_server_manager.objects.get(pk=field_id)
        if value=="True":
            value=True
        else:
            value=False
        data.online=value
        data.save()
        jiasu_conf_rsync()  #本地同步配置文件
        result={"code":0,"rid":field_id,"msg":"状态变更成功"}
    elif action=="change_group":
        data = accelerated_server_manager.objects.get(pk=field_id)
        data.platfrom=value
        data.save()
        result={"code":0,"rid":field_id,"msg":"属组变更成功"}
    elif action=="change_name":
        data = accelerated_server_manager.objects.get(pk=field_id)
        data.name=value
        data.save()
        result={"code":0,"rid":field_id,"msg":"名称已变更为:%s"% value}
    elif action=="change_date":
        try:
            data = accelerated_server_manager.objects.get(pk=field_id)
            data.stop_date=value
            data.save()
            result={"code":0,"rid":field_id,"msg":"到期时间已变更为:%s"% value}
        except:
            result["msg"]="时间格式错误,请遵循: YYYY-MM-DD 格式"
    elif action=="change_remark":
        data = accelerated_server_manager.objects.get(pk=field_id)
        data.remark=value
        data.save()
        result={"code":0,"rid":field_id,"msg":"备注已变更"}
    elif action=="change_master":
        if not isValidIp(value):
            result["msg"]="IP格式错误"
            return JsonResponse(result)
        if accelerated_server_manager.objects.filter(host_master=value):
            result["msg"]="IP地址已存在"
            return JsonResponse(result)
        data = accelerated_server_manager.objects.get(pk=field_id)
        data.host_master=value
        data.save()
        jiasu_conf_rsync()  #本地同步配置文件
        result={"code":0,"rid":field_id,"msg":"地址一变更为:%s"% value}
    elif action=="change_slave":
        if not isValidIp(value):
            result["msg"]="IP格式错误"
            return JsonResponse(result)
        data = accelerated_server_manager.objects.get(pk=field_id)
        data.host_slave=value
        data.save()
        result={"code":0,"rid":field_id,"msg":"地址二变更为:%s"% value}
    elif action=="init":
        ids = eval(field_id)
        if ids:
            for i in ids:
                data = accelerated_server_manager.objects.get(pk=i)
                try:
                    host=Server.objects.get(ssh_host=data.host_master)
                    jiasu_init_task.delay(host.ssh_host,host.ssh_port,host.ssh_user,host.ssh_password)
                    result={"code":1,"rid":ids,"msg":"%s 没有在CMDB中发现,停止初始化!"% data.host_master}
                except:
                    result={"code":1,"rid":ids,"msg":"%s 没有在CMDB中发现,停止初始化!"% data.host_master}
    elif action=="zabbix":
        ids = eval(field_id)
        if ids:
            zbx=zabbixtools("http://172.25.100.10/","zbxuser","zbxpass")
            if zbx.authID == 0: return JsonResponse({"code":1,"rid":ids,"msg":"zabbix认证失败!"})
            for i in ids:
                data = accelerated_server_manager.objects.get(pk=i)
                zbx.jiasu_host_create(data.host_master,"%s-加速-%s"% (data.name,data.host_master))
                zbx.jiasu_host_create(data.host_slave,"%s-加速-%s"% (data.name,data.host_slave))
            result={"code":0,"rid":ids,"msg":"IP已加入zabbix监控列表"}
    elif action=="sync":
        ids = eval(field_id)
        if ids:
            for i in ids:
                data = accelerated_server_manager.objects.get(pk=i)
                data.online=True
                data.save()
            jiasu_conf_rsync()  #本地同步配置文件
            result={"code":0,"rid":ids,"msg":"IP已加入同步列表"}
    else:
        pass
    return JsonResponse(result)


@login_required()
def acceleration_node_delete(request):
    ids=request.GET.get('ids')
    ids = eval(ids)
    result={"code":1,"rid":"","msg":"空值错误"}
    if ids:
        for i in ids:
            data = accelerated_server_manager.objects.get(pk=i)
            data.delete()
        jiasu_conf_rsync()  #本地同步配置文件
        result = {"code":0,"rid":ids,"msg":"数据已删除!"}
    return JsonResponse(result)