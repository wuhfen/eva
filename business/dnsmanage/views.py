#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required, permission_required
# from forms import BusinessForm, BugsForm
from business.models import dnsmanage_apikey,dnsmanage_name, dnsmanage_record,Business
from business.forms import DnsApiForm, DnsNameForm, DnsRecordForm
from .dnspod_api import DNSPod
from cloudxns.api import *
from api.common_api import isValidIp
try:
    import json
except ImportError:
    import simplejson as json
##账户增删查改
@permission_required('business.add_dnsmanage_apikey', login_url='/auth_error/')
def dnsuser_list(request):
    data = dnsmanage_apikey.objects.all()
    return render(request,'business/dnsuser_list.html',locals())

@permission_required('business.add_dnsmanage_apikey', login_url='/auth_error/')
def dnsuser_delete(request,id):
    data = dnsmanage_apikey.objects.get(pk=id)
    data.delete()
    return render(request,'business/dnsuser_list.html',locals())


@permission_required('business.add_dnsmanage_apikey', login_url='/auth_error/')
def dnsuser_add(request):
    bf = DnsApiForm()
    if request.method == 'POST':
        bf = DnsApiForm(request.POST)
        if bf.is_valid():
            bf_data = bf.save()
            return HttpResponseRedirect('/business/domain/manage/user/list/')
    return render(request,'business/dnsuser_add.html',locals())

@permission_required('business.add_dnsmanage_apikey', login_url='/auth_error/')
def dnsuser_edit(request,id):
    obj = get_object_or_404(dnsmanage_apikey, id=id)
    bf = DnsApiForm(instance=obj)
    if request.method == 'POST':
        bf = DnsApiForm(request.POST,instance=obj)
        if bf.is_valid():
            bf_data = bf.save(commit=False)
            bf_data.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'business/dnsuser_edit.html',locals())



def name_diff(name,name_id,status,user,records=None,ttl=None):
    if records:
        records = records
    else:
        records = 0
    if ttl:
        ttl = ttl
    else:
        ttl = 600
    try:
        obj = dnsmanage_name.objects.get(name_id=name_id)
        if obj.status is not status or obj.records is not records or obj.ttl is not ttl:
            dnsmanage_name.objects.filter(name_id=name_id).update(name=name,status=status,records=records,ttl=ttl)
    except dnsmanage_name.DoesNotExist:
        b = dnsmanage_name(name_id=name_id,name=name,status=status,user=user,records=records,ttl=ttl)
        b.save()



##同步域名数据，获取最新的域名信息导入数据库
def dnsuser_get_domainname(request,id):
    try:
        data = dnsmanage_apikey.objects.get(pk=id)
        namelist = [ i.name for i in  dnsmanage_name.objects.filter(user=data)]
    except dnsmanage_name.DoesNotExist:
        namelist = []
    get_domain_list = []
    if data.platform_name == "CLOUDXNS":
        api_key = data.keyone
        secret_key = data.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.domain_list())
        for i in result['data']:
            if type(i) == type({}):
                records = json.loads(dns.host_list(i['id']))
                records = records['total']
                name_diff(i['domain'].strip('.'),i['id'],i['status'],data,records,i['ttl'])
                get_domain_list.append(i['domain']) 
    else:
        user_token = data.keyone+","+data.keytwo
        dns = DNSPod(data.user,data.passwd,data.platform_name,user_token)
        res = dns.pod_domain_list()
        for i in res:
            if type(i) == type({}):
                name_diff(i['name'],i['id'],i['status'],data,i['records'],i['ttl'])
                get_domain_list.append(i['name'])
    for s in namelist:
        if s not in get_domain_list:
            dnsmanage_name.objects.get(name=s).delete()

    return HttpResponseRedirect('/business/domain/manage/user/list/')




##添加域名函数，先在平台添加，平台返回ture后，在数据库添加
def domain_add_to_palt_and_db(domain,user_id,platform=None,remark=None):
    data = dnsmanage_apikey.objects.get(pk=user_id)
    success = []
    false = []
    msg = None
    if not platform:
        platform = data.platform_name
    if platform == 'PODCN':
        user_token = data.keyone+","+data.keytwo
        dns = DNSPod(data.user,data.passwd,platform,str(user_token))
        dns.pod_domain_list()
        if ',' in domain:
            domainlist = domain.split(',')
            for i in domainlist:
                res = dns.pod_domain_add(i)
                if res["status"]["code"] == "1":
                    domain_id = res["domain"]["id"]
                    b = dnsmanage_name(name_id=domain_id,name=i,status="enable",user=data,records='3',ttl='600',remark=remark)
                    b.save()
                    success.append(i)
                else:
                    false.append(i)
                    msg = res["status"]["message"]
            if msg:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败！<br>原因：%s"% (len(success),len(false),','.join(success),','.join(false),msg)
            else:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败！"% (len(success),len(false),','.join(success),','.join(false))
        else:
            res = dns.pod_domain_add(domain)
            if res["status"]["code"] == "1":
                domain_id = res["domain"]["id"]
                info = dns.pod_domain_info(domain_id)
                if info["status"]["code"] == "1":
                    info = info["domain"]
                    b = dnsmanage_name(name_id=domain_id,name=domain,status=info["status"],user=data,records=info["records"],ttl=info["ttl"],remark=remark)
                    b.save()
                    result = "域名：%s <br>返回：添加成功！"% domain
                else:
                    result = info["status"]["message"]
            else:
                result = res["status"]["message"]
    elif platform == 'PODCOM':
        dns = DNSPod(data.user,data.passwd,data.platform_name)
        if ',' in domain:
            domainlist = domain.split(',')
            for i in domainlist:
                res = dns.pod_domain_add(i)
                if res["status"]["code"] == "1":
                    domain_id = res["domain"]["id"]
                    b = dnsmanage_name(name_id=domain_id,name=i,status="enable",user=data,records='3',ttl='600',remark=remark)
                    b.save()
                    success.append(i)
                else:
                    false.append(i)
                    msg = res["status"]["message"]
            if msg:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败！<br>原因：%s"% (len(success),len(false),','.join(success),','.join(false),msg)
            else:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败！"% (len(success),len(false),','.join(success),','.join(false))
        else:
            res = dns.pod_domain_add(domain)
            print res
            if res["status"]["code"] == "1":
                domain_id = res["domain"]["id"]
                info = dns.pod_domain_info(domain_id)
                print info
                if info["status"]["code"] == "1":
                    info = info["domain"]
                    b = dnsmanage_name(name_id=domain_id,name=domain,status=info["status"],user=data,records=info["records"],ttl=info["ttl"],remark=remark)
                    b.save()
                    result = "域名：%s <br>返回：添加成功！"% domain
                else:
                    result = info["status"]["message"]
            else:
                result = res["status"]["message"]
    else:
        api_key = data.keyone
        secret_key = data.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        if ',' in domain:
            domainlist = domain.split(',')
            for i in domainlist:
                res = json.loads(dns.domain_add(i))
                if res['code'] == 1:
                    b = dnsmanage_name(name_id=res["id"],name=i,status="ok",user=data,records='0',ttl='600',remark=remark)
                    b.save()
                    success.append(i)
                else:
                    false.append(i)
                    msg = res["message"]
            if msg:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败！<br>原因：%s"% (len(success),len(false),','.join(success),','.join(false),msg)
            else:
                result = "成功%d条域名，失败%d条域名<br>域名：%s <br>返回：添加成功！<br>域名：%s <br>返回：添加失败! "% (len(success),len(false),','.join(success),','.join(false))
        else:
            res = json.loads(dns.domain_add(domain))
            if res['code'] == 1:
                b = dnsmanage_name(name_id=res["id"],name=domain,status="ok",user=data,records='0',ttl='600',remark=remark)
                b.save()
                result = "域名：%s <br>返回：添加成功！"% domain
            else:
                result = res["message"]
    return result





##域名增删查改
@permission_required('business.add_dnsmanage_name', login_url='/auth_error/')
def dnsname_add_one(request):
    data = dnsmanage_apikey.objects.filter(status=True)
    if request.method == 'POST':
        msg_errors = []
        remark = request.POST.get('remark')
        platform = request.POST.get('platform')
        user_id = request.POST.get('user_id')
        user_obj = dnsmanage_apikey.objects.get(pk=user_id)
        alldomainlist = [i.name  for i in dnsmanage_name.objects.filter(user=user_obj)]
        domainlist = request.POST.get('domain_name').strip().split()
        for i in domainlist:
            if '.' not in i:
                print i
                msg = u"域名:%s <br>错误：域名格式错误！"% i
                msg_errors.append(msg)
                return JsonResponse({'retu':"False",'msg':msg_errors})
            if i in alldomainlist:
                msg = u"域名:%s <br>错误：域名已存在！"% i
                msg_errors.append(msg)
                return JsonResponse({'retu':"False",'msg':msg_errors})
        if len(domainlist) > 1:
            domainlist = ','.join(domainlist)
        else:
            domainlist = domainlist[0]
        res = domain_add_to_palt_and_db(domainlist,user_id,platform,remark)
        return JsonResponse({'retu':"True",'res':res})
    return render(request,'business/dnsname_add_one.html',locals())

##改变域名状态
@permission_required('business.change_dnsmanage_name', login_url='/auth_error/')
def dnsname_status_change(request):
    data_id = request.GET.get('uuid','')
    obj = dnsmanage_name.objects.get(pk=data_id)
    user_obj = obj.user

    old_status = obj.status
    if old_status == "enable":#userlock
        new_status = "disable"
        save_status = "pause"
    else:
        new_status = "enable"
        save_status = "enable"
    user_token = user_obj.keyone+","+user_obj.keytwo
    dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
    res = dns.pod_domain_status(new_status,str(obj.name_id))  #在dnspod上改变域名状态
    if res == "1":
        dnsmanage_name.objects.filter(pk=data_id).update(status=save_status)
        if save_status == "pause":
            result = {'res':"OK",'status':"启用",'info':save_status}
        else:
            result = {'res':"OK",'status':"禁用",'info':save_status}
    else:
        result = {'res':"fail",'msg':res["status"]["message"]}
    return JsonResponse(result,safe=False)
    # return JsonResponse({'resd':"OK",'status':"禁用"},safe=False)

@permission_required('business.delete_dnsmanage_name',login_url='/auth_error/')
def dnsname_delete(request,id):
    """删除域名，为了确保安全，不写批量删除"""
    obj = dnsmanage_name.objects.get(pk=id)
    user_obj = obj.user
    platform_name = user_obj.platform_name
    if platform_name == "CLOUDXNS":
        api_key = user_obj.keyone
        secret_key = user_obj.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.domain_delete(obj.name_id))
        if result["code"] == 1:
            result = {'res':"OK",'info':"删除成功！"}
            obj.delete()
        else:
            result = {'res':"fail",'info':"删除失败！原因：" + result["message"]}
    else:
        user_token = user_obj.keyone+","+user_obj.keytwo
        dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
        res = dns.pod_domain_delete(str(obj.name_id))  #在dnspod上删除域名
        if res == '1':
            result = {'res':"OK",'info':"删除成功！"}
            obj.delete()
        else:
            result = {'res':"fail",'info':"删除失败！原因：" + res["message"]}

    return JsonResponse(result,safe=False)

@permission_required('business.add_dnsmanage_name',login_url='/auth_error/')
def dnsname_detail(request,id):
    obj = dnsmanage_name.objects.get(pk=id)
    data = dnsmanage_record.objects.filter(domain=obj)
    return render(request,'business/dnsname_detail.html',locals())

@permission_required('business.delete_dnsmanage_name',login_url='/auth_error/')
def dnsname_transfer(request,uuid):
    obj = dnsmanage_name.objects.get(pk=uuid)
    record_objs = obj.SUBRECORD.all()
    data = dnsmanage_apikey.objects.all()
    error_msgs = []

    if request.method == 'POST':
        user_id = request.POST.get('user_id','')
        new_user_obj = dnsmanage_apikey.objects.get(pk=user_id)
        #初始化cloudxns-api
        api_key = new_user_obj.keyone
        secret_key = new_user_obj.keytwo
        cdns = Api(api_key=api_key, secret_key=secret_key)
        #初始化dnspod-api
        user_token = new_user_obj.keyone+","+new_user_obj.keytwo
        pdns = DNSPod(new_user_obj.user,new_user_obj.passwd,new_user_obj.platform_name,user_token)
        #step1 删除线上老数据
        if obj.user.platform_name == "CLOUDXNS":
            api_key = obj.user.keyone
            secret_key = obj.user.keytwo
            dns = Api(api_key=api_key, secret_key=secret_key)
            result = json.loads(dns.domain_delete(obj.name_id))
            if result['code'] != 1:
                return JsonResponse({'res': "Fail",'info': result["message"]})
        else:
            user_token = obj.user.keyone+","+obj.user.keytwo
            dns = DNSPod(obj.user.user,obj.user.passwd,obj.user.platform_name,user_token)
            res = dns.pod_domain_delete(str(obj.name_id))
            if res != "1":
                return JsonResponse({'res': "Fail",'info': res["message"]})
        #step2 更改数据库中的user字段为新用户
        dnsmanage_name.objects.filter(pk=uuid).update(user=new_user_obj)
        #step3 新账号线上添加域名,成功后更新name_id字段
        if new_user_obj.platform_name == "CLOUDXNS":
            res = json.loads(cdns.domain_add(obj.name))
            if res['code'] == 1:
                domain_id = res["id"]
                dnsmanage_name.objects.filter(pk=uuid).update(name_id=domain_id)
            else:
                error_msgs.append("Cloudxns快网添加域名失败，原因：%s"% res["message"])
                return JsonResponse({'res': "Fail",'info': res["message"]})
        else:
            res = pdns.pod_domain_add(obj.name)
            if res["status"]["code"] == "1":
                domain_id = res["domain"]["id"]
                dnsmanage_name.objects.filter(pk=uuid).update(name_id=domain_id)
            else:
                error_msgs.append("DNSPod添加域名失败，原因：%s"% res["status"]["message"])
                return JsonResponse({'res': "Fail",'info': res["status"]["message"]})
        #step4 新账号中添加记录，成功后更新record_id,host_id
        if len(record_objs) > 0:
            for i in record_objs:
                subdomain = i.subdomain
                recordtype = i.record_type
                recordvalue = i.value
                recordttl = i.ttl
                standby = i.standby
                status = i.status
                if recordtype != "NS":
                    if new_user_obj.platform_name == "CLOUDXNS":
                        res = json.loads(cdns.record_add(domain_id,subdomain,recordvalue,recordtype,55,recordttl,1))
                        if res["code"] == 1:
                            print res
                            record_id = res["record_id"][0]
                            dnsmanage_record.objects.filter(pk=i.uuid).update(record_id=record_id)
                            cdns.record_status(domain_id,record_id,status)
                        else:
                            error_msgs.append("Cloudxns快网添加记录失败，原因：%s"% res["message"])
                            return JsonResponse({'res': "Fail",'info': res["message"]})
                    else:
                        res = pdns.pod_record_add(str(domain_id),subdomain,recordtype,recordvalue,ttl=recordttl)
                        if res["status"]["code"] == "1":
                            print res
                            record_id = res["record"]["id"]
                            dnsmanage_record.objects.filter(pk=i.uuid).update(record_id=record_id)
                            pdns.pod_record_status(str(domain_id),str(record_id),status)
                        else:
                            error_msgs.append("DNSPod添加记录失败，原因：%s"% res["status"]["message"])
                            return JsonResponse({'res': "Fail",'info': res["status"]["message"]})
        return JsonResponse({'res': "OK",'info': "成功！"})

    return render(request,'business/dnsname_transfer.html',locals())

@permission_required('business.add_dnsmanage_name', login_url='/auth_error/')
def dnsname_list(request):
    dnsusers = dnsmanage_apikey.objects.filter(status=True)
    datalist = []
    for i in dnsusers:
        datalist.append(i.user)
    data = dnsmanage_name.objects.all()

    return render(request,'business/dnsname_list1.html',locals())

##更新record记录，如果线上没有，数据库中有就删除，线上有，db无就增加，两边不一致，更新db数据
def update_record_to_db(record_id,subdomain,domain,record_type,value,ttl,status,standby=None,group=None,remark=None,host_id=None):
    try:
        obj = dnsmanage_record.objects.get(record_id=record_id)
        if not remark:
            remark = obj.remark
            # print remark
        if not group:
            group = obj.group
        if not standby:
            standby = obj.standby
        if not host_id:
            host_id = obj.host_id
        if obj.status is not status or obj.domain is not domain or obj.subdomain is not subdomain or obj.ttl is not ttl or obj.record_type is not record_type or obj.value is not value:
            dnsmanage_record.objects.filter(record_id=record_id).update(subdomain=subdomain,status=status,domain=domain,record_type=record_type,ttl=ttl,value=value,standby=standby,group=group,remark=remark,host_id=host_id)
    except dnsmanage_record.DoesNotExist:
        b = dnsmanage_record(record_id=record_id,subdomain=subdomain,domain=domain,status=status,record_type=record_type,value=value,standby=standby,ttl=ttl,group=group,remark=remark,host_id=host_id)
        b.save()

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_get_records(request,id):
    obj = dnsmanage_name.objects.get(pk=id)
    user_obj = obj.user
    plat = user_obj.platform_name
    records = [ i.record_id for i in obj.SUBRECORD.all() ]
    hosts = [ i.host_id for i in obj.SUBRECORD.all() ]
    # print hosts
    data = dnsmanage_record.objects.filter(domain=obj)
    online_records = []
    if plat == "CLOUDXNS":
        api_key = user_obj.keyone
        secret_key = user_obj.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.record_list(str(obj.name_id),row_num=1000))
        print result
        if result['code'] == 1:
            # print result['data']
            for i in result['data']:    #更新子域名数据，添加新数据
                # print i['host_id']
                online_records.append(i['record_id'])
                if i.has_key('spare_value'):
                    standby = i['spare_value']
                else:
                    standby = None
                if i['status'] == 'ok':
                    status = True
                else:
                    status = False
                update_record_to_db(i['record_id'],i['host'],obj,i['type'],i['value'],i['ttl'],status,standby,host_id=i['host_id'])
            # print online_records
            if len(records) > 0:
                for j in records:  #删除子域名旧数据
                    if str(j) not in online_records:
                        dnsmanage_record.objects.get(record_id=j).delete()
            dnsmanage_name.objects.filter(pk=id).update(records=len(online_records))
        elif result['code'] == 2:
            obj.SUBRECORD.all().delete()
        else:
            print result['message']
            msgerror = "错误：%s"% result['message']
    else:
        user_token = user_obj.keyone+","+user_obj.keytwo
        dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
        res = dns.pod_record_list(obj.name_id)  #获取域名记录在dnspod上
        print res
        if res["status"]["code"] == '1':
            # print res["info"]["record_total"]
            dnsmanage_name.objects.filter(pk=id).update(records=res["info"]["record_total"])
            for i in res["records"]:     #更新子域名数据，添加新数据
                online_records.append(i['id'])
                if i['enabled'] == '1':
                    status = True
                else:
                    status = False
                print status
                update_record_to_db(i['id'],i['name'],obj,i['type'],i['value'],i['ttl'],status)
            # print online_records
            # print type(online_records[0])
            if len(records) > 0:
                for j in records:  #删除子域名旧数据
                    if str(j) not in online_records:
                        dnsmanage_record.objects.get(record_id=j).delete()
        else:
            print res['status']['message']
            msgerror = "错误：%s"% res['status']['message']

    return render(request,'business/reback.html',locals())

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_add_records(request,id):
    """给域名多条记录"""
    obj = dnsmanage_name.objects.get(pk=id)
    user_obj = obj.user
    error_msgs = []
    success_msgs = []
    domain_type = ['A','CNAME','MX','NS']
    if request.method == 'POST':
        getrecords = request.POST.get('records','')
        if not getrecords:
            error_msgs.append("你没有填写任何数据！")
            return render(request,'business/dnsname_record_add.html',locals())
        records = getrecords.split('\r\n')
        records_list = []
        if len(records) == 1 and len(records[0].split()) < 3:
            error_msgs.append("缺少关键数据!")
            return render(request,'business/dnsname_record_add.html',locals())
        for i in records:
            if i.split()[1] == "A":
                if not isValidIp(i.split()[2]):
                    error_msgs.append("IP格式错误：%s"% i.split()[2])
            if i.split()[1] not in domain_type:
                error_msgs.append("记录类型只能是：A、CNAME、MX、NS，不支持：%s"% i.split()[1])
            records_list.append({"subdomain": i.split()[0],"type":i.split()[1],"value": i.split()[2]})
        if len(error_msgs) > 0:
            return render(request,'business/dnsname_record_add.html',locals())
        status = True
        if user_obj.platform_name == "CLOUDXNS":
            api_key = user_obj.keyone
            secret_key = user_obj.keytwo
            dns = Api(api_key=api_key, secret_key=secret_key)
            for i in records_list:
                result = json.loads(dns.record_add(obj.name_id,i["subdomain"],i["value"],i["type"],55,600,1))  #cloudxns添加记录
                print result
                if result["code"] == 1:
                    record_id = result["record_id"]
                    result = {'retu':"OK",'info':"%s --> %s 添加成功！"% (i["subdomain"],i["value"])}
                    success_msgs.append(result)
                    update_record_to_db(record_id[0],i["subdomain"],obj,i["type"],i["value"],600,status) #数据库保存
                else:
                    error_msgs.append("%s --> %s 添加失败！原因：%s"% (i["subdomain"],i["value"],result["message"]))
        else:
            user_token = user_obj.keyone+","+user_obj.keytwo
            dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
            for i in records_list:
                res = dns.pod_record_add(str(obj.name_id),i["subdomain"],i["type"],i["value"],ttl='600')  #在dnspod上添加记录
                print res
                if res["status"]["code"] == "1":
                    if res.has_key('record'):
                        record_id = res["record"]["id"]
                        update_record_to_db(record_id,i["subdomain"],obj,i["type"],i["value"],600,status) #数据库保存
                        result = {'retu':"OK",'info':"%s --> %s 添加成功！"% (i["subdomain"],i["value"])}
                        success_msgs.append(result)
                else:
                    error_msgs.append("%s --> %s 添加失败！原因：%s"% (i["subdomain"],i["value"],res["status"]["message"]))
    return render(request,'business/dnsname_record_add.html',locals())

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_add_one_record(request,id):
    """添加一条记录"""
    obj = dnsmanage_name.objects.get(pk=id)
    user_obj = obj.user
    platform_name = user_obj.platform_name
    # rf = DnsRecordForm()
    business = Business.objects.all()
    if request.method == 'POST':
        subdomain = request.POST.get('subdomain')
        recordtype = request.POST.get('type')
        recordvalue = request.POST.get('value')
        recordttl = request.POST.get('ttl')
        remark = request.POST.get('remark')
        group = request.POST.get('group')
        group = Business.objects.get(pk=group)
        print "备注：%s"% remark
        if platform_name == "CLOUDXNS":
            api_key = user_obj.keyone
            secret_key = user_obj.keytwo
            dns = Api(api_key=api_key, secret_key=secret_key)
            result = json.loads(dns.record_add(obj.name_id,subdomain,recordvalue,recordtype,55,recordttl,1))  #cloudxns添加记录
            if result["code"] == 1:
                # print result
                record_id = result["record_id"]
                # print type(record_id)
                status = True
                result = {'retu':"OK",'info':"添加成功！"}
                update_record_to_db(record_id[0],subdomain,obj,recordtype,recordvalue,recordttl,status,group=group,remark=remark) #数据库保存
                return JsonResponse(result)

            else:
                result = {'retu':"fail",'info':"添加失败！原因：" + result["message"]}
                return JsonResponse(result)
        # print subdomain,recordtype,recordvalue,recordttl,remark
        else:
            user_token = user_obj.keyone+","+user_obj.keytwo
            dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
            res = dns.pod_record_add(str(obj.name_id),subdomain,recordtype,recordvalue,ttl=recordttl)  #在dnspod上添加记录
            print res
            if res["status"]["code"] == "1":
                if res.has_key('record'):
                    record_id = res["record"]["id"]
                    status = True
                    update_record_to_db(record_id,subdomain,obj,recordtype,recordvalue,recordttl,status,group=group,remark=remark) #数据库保存
                    result = {'retu':"OK",'info':"添加成功！"}
                    return JsonResponse(result)
            result = {'retu':"fail",'info':"添加失败！原因：" + res["status"]["message"]}
            return JsonResponse(result,safe=False)

    return render(request,'business/dnsname_record_add_one.html',locals())

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_modify(request,uuid):
    """修改一条记录"""
    data = dnsmanage_record.objects.get(pk=uuid)
    obj = data.domain
    user_obj = obj.user
    business = Business.objects.all()
    platform_name = user_obj.platform_name

    if request.method == 'POST':
        subdomain = request.POST.get('subdomain')
        recordtype = request.POST.get('type')
        recordvalue = request.POST.get('value')
        recordstandby = request.POST.get('standby')
        recordttl = request.POST.get('ttl')
        remark = request.POST.get('remark')
        group = request.POST.get('group')
        if not group:
            result = {'retu':"fail",'info':"组不能为空！"}
            return JsonResponse(result)
        group = Business.objects.get(pk=group)
        status = data.status
        if subdomain == data.subdomain and recordtype == data.record_type and recordvalue == data.value and recordttl == data.ttl:
            dnsmanage_record.objects.filter(pk=uuid).update(remark=remark,group=group,standby=recordstandby)
            result = {'retu':"OK",'info':"更新成功！"}
            return JsonResponse(result)
        if platform_name == "CLOUDXNS":
                api_key = user_obj.keyone
                secret_key = user_obj.keytwo
                dns = Api(api_key=api_key, secret_key=secret_key)
                result = json.loads(dns.record_update(data.record_id,obj.name_id,subdomain,recordvalue,recordtype,55,recordttl,1,recordstandby))  #cloudxns更新记录
                if result["code"] == 1:
                    print result
                    record_id = result["data"]["id"]
                    # print type(record_id)
                    result = {'retu':"OK",'info':"更新成功！"}
                    update_record_to_db(record_id,subdomain,obj,recordtype,recordvalue,recordttl,status,recordstandby,group=group,remark=remark) #数据库保存
                    return JsonResponse(result)
                else:
                    result = {'retu':"fail",'info':"更新失败！原因：" + result["message"]}
                    return JsonResponse(result)
        else:
            user_token = user_obj.keyone+","+user_obj.keytwo
            dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
            res = dns.pod_record_modify(str(obj.name_id),str(data.record_id),subdomain,recordtype,recordvalue,ttl=recordttl)  #在dnspod上更新记录
            print res
            if res["status"]["code"] == "1":
                if res.has_key('record'):
                    record_id = res["record"]["id"]
                    update_record_to_db(record_id,subdomain,obj,recordtype,recordvalue,recordttl,status,recordstandby,group=group,remark=remark) #数据库保存
                    result = {'retu':"OK",'info':"更新成功！"}
                    return JsonResponse(result)
                else:
                    update_record_to_db(data.record_id,subdomain,obj,recordtype,recordvalue,recordttl,status,recordstandby,group=group,remark=remark)
                    result = {'retu':"OK",'info':"更新数据成功！"}
                    return JsonResponse(result)
            result = {'retu':"fail",'info':"更新失败！原因：" + res["status"]["message"]}
            return JsonResponse(result,safe=False)

    return render(request,'business/dnsname_record_modify.html',locals())

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_delete(request,uuid):
    """删除子域名记录"""
    data = dnsmanage_record.objects.get(pk=uuid)
    obj = data.domain
    user_obj = obj.user
    business = Business.objects.all()
    platform_name = user_obj.platform_name
    if platform_name == "CLOUDXNS":
        api_key = user_obj.keyone
        secret_key = user_obj.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.record_delete(data.record_id,obj.name_id))  #cloudxns删除记录
        if result["code"] == 1:
            data.delete() #数据库删除记录
            result = {'retu':"OK",'info':"删除成功！"}
        else:
            result = {'retu':"fail",'info':"无法删除！原因：" + result["message"]}
        return JsonResponse(result)
    else:
        user_token = user_obj.keyone+","+user_obj.keytwo
        dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
        res = dns.pod_record_remove(str(obj.name_id),str(data.record_id))  #在dnspod上更新记录
        print res
        if res == "1":
            data.delete()
            result = {'retu':"OK",'info':"删除成功！"}
        else:
            result = {'retu':"fail",'info':"无法删除！原因：" + res["message"]}
        return JsonResponse(result,safe=False)
    return JsonResponse({'retu':"NOTHING",'info':"啥都没干！"},safe=False)

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_domain_remark(request):
    """更新域名备注"""
    uuid = request.GET.get('id','')
    remark = request.GET.get('remark','')
    domain_obj = dnsmanage_name.objects.get(pk=uuid)
    print uuid,remark,domain_obj.name
    dnsmanage_name.objects.filter(pk=uuid).update(remark=remark)

    return JsonResponse({'retu':"OK",'info':"已更新备注！"},safe=False)


@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_standby(request):
    """添加备用IP,下面注释掉是因为cloudxns提供了添加方法没有提供切换方法，我使用更新主IP的方式实现切换，必须保证没有备IP干扰"""
    uuid = request.GET.get('uuid','')
    # objid = request.GET.get('objid','')
    standby = request.GET.get('standby','')
    data = dnsmanage_record.objects.get(pk=uuid)
    # obj = dnsmanage_name.objects.get(pk=objid)
    # user_obj = obj.user
    # platform_name = user_obj.platform_name

    # if platform_name == "CLOUDXNS":
    #     api_key = user_obj.keyone
    #     secret_key = user_obj.keytwo
    #     dns = Api(api_key=api_key, secret_key=secret_key)
    #     result = json.loads(dns.record_spare(obj.name_id,data.host_id,data.record_id,standby))  #cloudxns添加备记录
    #     print result
    #     if result["code"] == 1:
    #         dnsmanage_record.objects.filter(pk=uuid).update(standby=standby)
    #         result = {'res':"OK",'info':"备用值添加成功！"}
    #     else:
    #         result = {'res':"fail",'info':"添加失败！原因：" + result["message"]}
    #     return JsonResponse(result)
    dnsmanage_record.objects.filter(pk=uuid).update(standby=standby)
    result = {'res':"OK",'info':"备用值添加成功！"}
    return JsonResponse(result)

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_switcher(request):
    """切换主备IP"""
    uuid = request.GET.get('uuid','')
    # objid = request.GET.get('objid','')
    # obj = dnsmanage_name.objects.get(pk=objid)
    data = dnsmanage_record.objects.get(pk=uuid)
    obj = data.domain
    user_obj = obj.user
    platform_name = user_obj.platform_name
    if platform_name == "CLOUDXNS":
        api_key = user_obj.keyone
        secret_key = user_obj.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.record_update(data.record_id,obj.name_id,data.subdomain,data.standby,data.record_type,55,data.ttl,1))  #cloudxns切换ip就是更新记录的动作
        print result

        if result["code"] == 1:
            result = {'retu':"OK",'info':"切换成功！"}
            dnsmanage_record.objects.filter(pk=uuid).update(value=data.standby,standby=data.value)
            return JsonResponse(result)
        result = {'retu':"fail",'info':"切换失败！原因：" + result["message"]}
        return JsonResponse(result)
    else:
        user_token = user_obj.keyone+","+user_obj.keytwo
        dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
        res = dns.pod_record_modify(str(obj.name_id),str(data.record_id),data.subdomain,data.record_type,data.standby,ttl=data.ttl)  #在dnspod上更新记录
        print res
        if res["status"]["code"] == "1":
            dnsmanage_record.objects.filter(pk=uuid).update(value=data.standby,standby=data.value)
            result = {'res':"OK",'info':"切换成功！"}
            return JsonResponse(result)

        result = {'res':"fail",'info':"切换失败！原因：" + res["status"]["message"]}
        return JsonResponse(result,safe=False)

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_list(request):
    """记录列表"""
    record_objs = dnsmanage_record.objects.all()


    return render(request,'business/record_list.html',locals())

@permission_required('business.add_dnsmanage_record', login_url='/auth_error/')
def dnsname_record_status(request):
    """禁用启用一条记录，dnspod有自己的api，cloudxns自己写了状态更新在/usr/lib/python2.7/site-packages/cloudxns/api.py"""
    uuid = request.GET.get('uuid','')
    record_obj = dnsmanage_record.objects.get(pk=uuid)
    domain_obj = record_obj.domain
    user_obj = domain_obj.user
    platform = user_obj.platform_name

    status = record_obj.status
    print status
    print type(status)
    if status == True:
        new_status = False
    else:
        new_status = True
    print new_status
    if platform == 'CLOUDXNS':
        api_key = user_obj.keyone
        secret_key = user_obj.keytwo
        dns = Api(api_key=api_key, secret_key=secret_key)
        result = json.loads(dns.record_status(domain_obj.name_id,record_obj.record_id,new_status))
        print result
        if result["code"] == 1:
            result = {'res':"OK",'info':"记录状态已变更！"}
            dnsmanage_record.objects.filter(pk=uuid).update(status=new_status)
        else:
            result = {'res':"fail",'info':"状态变更失败！原因：%s"% result['message']}
    else:
        user_token = user_obj.keyone+","+user_obj.keytwo
        dns = DNSPod(user_obj.user,user_obj.passwd,user_obj.platform_name,user_token)
        res = dns.pod_record_status(str(domain_obj.name_id),str(record_obj.record_id),new_status)  #在dnspod上更新记录
        print res
        if res["status"]["code"] == "1":
            result = {'res':"OK",'info':"记录状态已变更！"}
            dnsmanage_record.objects.filter(pk=uuid).update(status=new_status)
        else:
            result = {'res':"fail",'info':"状态变更失败！原因：%s"% + res["status"]["message"]}
    return JsonResponse(result,safe=False)
