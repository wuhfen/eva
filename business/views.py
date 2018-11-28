#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required, permission_required
# from forms import BusinessForm
from models import Business,DomainName,Domain_ip_pool,DomainInfo
from forms import BusinessForm, DomainNameForm,IPpoolForm
from api.ansible_api import ansiblex_domain
from api.ssh_api import ssh_cmd

from Allow_list.models import Iptables
from assets.models import Server,Project
import time
import json
from tempfile import NamedTemporaryFile
import os

from .tasks import monitor_code


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
            siteid = bf_data.nic_name
            #需要创建测试环境和灰度环境的域名,傻啊，都不分现金网和蛮牛吗？
            if bf_data.platform == "现金网":
                test_f = DomainName(name=siteid+".test.s1118.com",use=0,business=bf_data,classify="test",state=0,supplier="工程")
                test_f.save()
                huidu_f = DomainName(name=siteid+".s1119.com",use=0,business=bf_data,classify="huidu",state=0,supplier="运维")
                huidu_a = DomainName(name="ag"+siteid+".s1119.com",use=1,business=bf_data,classify="huidu",state=0,supplier="运维")
                huidu_a.save()
                huidu_f.save()
            elif bf_data.platform == "蛮牛":
                huidu_f = DomainName(name=siteid+".kg-44.com",use=0,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a = DomainName(name="ag"+siteid+".kg-44.com",use=1,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a.save()
                huidu_f.save()
            elif bf_data.platform == "VUE蛮牛":
                huidu_f = DomainName(name=siteid.replace("vue","")+".kg-8.me",use=0,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a = DomainName(name="ag"+siteid+".kg-8.me",use=1,business=bf_data,classify="huidu",state=0,supplier="工程")
                huidu_a.save()
                huidu_f.save()
            return HttpResponseRedirect('/allow/welcome/')
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


##域名增删查改
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
            return render(request,'business/domain_add_select.html',locals())
        # if use == '2':
        #     pool = Domain_ip_pool.objects.get(name="新站后台反代")
        # elif use == '1':
        #     pool = Domain_ip_pool.objects.get(name="新站第三方ag反代")
        # else:
        #     pool = Domain_ip_pool.objects.get(name="CDN（抗攻击）")
        for i in domainname.split('\r\n'):
            save_data = DomainName(name=i.strip(),use=use,business=business,state='0',classify=classify,supplier=supplier,monitor_status=False)
            save_data.save()
    return render(request,'business/domain_add_select.html',locals())



def domain_edit(request,uuid):
    domainname = get_object_or_404(DomainName, uuid=uuid)
    df = DomainNameForm(instance=domainname)
    if request.method == 'POST':
        df = DomainNameForm(request.POST,instance=domainname)
        if df.is_valid():
            df_data = df.save()
            return HttpResponseRedirect('/allow/welcome/')
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

from models import accelerated_server_manager
def acceleration_node_add(request):
    try:
        pro = Project.objects.get(project_name="加速服务器")
        servers = pro.project_servers.all()
        available_servers =[ i for i in servers if i.asset.status == 'on']
    except:
        available_servers = None
    if request.method == "POST":
        name = request.POST.get('name')
        host = request.POST.get('ip')
        domains = request.POST.get('domain')
        purchase_date = request.POST.get('purchase_date')
        stop_date = request.POST.get('stop_date')
        remark = request.POST.get('remark')
        if not purchase_date:
            purchase_date = None
        if not stop_date:
            stop_date = None
        data = accelerated_server_manager(name=name,host=host,domains=domains,purchase_date=purchase_date,stop_date=stop_date,remark=remark)
        data.save()
        return JsonResponse({'res':"OK"},safe=False)
    return render(request,'business/acceleration_node_add.html',locals())

def acceleration_node_list(request):
    data = accelerated_server_manager.objects.all()
    return render(request,'business/acceleration_node_list.html',locals())

def acceleration_node_delete(request,uuid):
    data = accelerated_server_manager.objects.get(pk=uuid)
    data.delete()
    result = {"status":"success","info":"Deleted"}
    return JsonResponse(result)

def acceleration_node_modify(request,uuid):
    data = accelerated_server_manager.objects.get(pk=uuid)

    if request.method == "POST":
        name = request.POST.get('name')
        host = request.POST.get('ip')
        domains = request.POST.get('domain')
        purchase_date = request.POST.get('purchase_date')
        stop_date = request.POST.get('stop_date')
        remark = request.POST.get('remark')
        if not purchase_date:
            purchase_date = None
        if not stop_date:
            stop_date = None
        data.name = name
        data.host = host
        data.domains = domains
        data.purchase_date = purchase_date
        data.stop_date = stop_date
        data.remark = remark
        data.save()
        result = {"res":"OK","status":"success","info":"Modify"}
        return JsonResponse(result)
    return render(request,'business/acceleration_node_modify.html',locals())