#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from automation.models import gengxin_code,gengxin_deploy,AUser
from automation.forms import gengxin_codeForm
# Create your views here.
import time
from .tasks import gengxin_update_task,fabu_update_task,fabu_nginxconf_task

from accounts.models import CustomUser
from automation.gengxin_deploy import website_deploy
from business.models import Business

@login_required
def gengxin_code_list(request):
    data = gengxin_code.objects.all()
    return render(request, 'automation/gengxin_code_list.html', locals())

@login_required
def gengxin_code_add(request):
    Users = CustomUser.objects.all()
    tf = gengxin_codeForm()
    if request.method == 'POST':
        tf = gengxin_codeForm(request.POST)
        mergedir = request.POST.get('mergedir')
        classify = request.POST.get('classify')
        if gengxin_code.objects.filter(classify=classify).filter(name=request.POST.get('name')):
            errors = "已有此名称，不能重复！"
            return render(request, 'automation/gengxin_code_add.html', locals())
        if gengxin_code.objects.filter(classify=classify).filter(business=request.POST.get('business')):
            errors = "已有发布关联到此业务，不能重复！"
            return render(request, 'automation/gengxin_code_add.html', locals())
        if tf.is_valid():
            tf_data = tf.save()
            print "tf_data="+tf_data.remoteip
            fabu = fabu_update_task.delay(tf_data.uuid)
            configurate = fabu_nginxconf_task.delay(tf_data.uuid)
            return HttpResponseRedirect('/deploy/gengxin_code_list/')
    return render(request, 'automation/gengxin_code_add.html', locals())

@login_required
def git_gengxin_code_add(request):
    Users = CustomUser.objects.all()
    tf = gengxin_codeForm()
    data = Business.objects.all()
    # if request.method == 'POST':
    #     tf = gengxin_codeForm(request.POST)
    #     mergedir = request.POST.get('mergedir')
    #     classify = request.POST.get('classify')
    #     if gengxin_code.objects.filter(classify=classify).filter(name=request.POST.get('name')):
    #         errors = "已有此名称，不能重复！"
    #         return render(request, 'automation/gengxin_code_add.html', locals())
    #     if gengxin_code.objects.filter(classify=classify).filter(business=request.POST.get('business')):
    #         errors = "已有发布关联到此业务，不能重复！"
    #         return render(request, 'automation/gengxin_code_add.html', locals())
    #     if tf.is_valid():
    #         tf_data = tf.save()
    #         print "tf_data="+tf_data.remoteip
    #         fabu = fabu_update_task.delay(tf_data.uuid)
    #         configurate = fabu_nginxconf_task.delay(tf_data.uuid)
    #         return HttpResponseRedirect('/deploy/gengxin_code_list/')
    return render(request, 'automation/git_gengxin_code_add.html', locals())

def git_return_deploy_info(request,uuid):
    index = uuid.split('_')[-1]
    env = uuid.split('_')[0]
    data = Business.objects.get(pk=index)
    if uuid.split('_')[0] == 'huidu':
        webd = [data.nic_name+".s1119.com"]
        agd = ["ag"+data.nic_name+".s1119.com"]
    else:
        webd = [x.name for x in data.domain.filter(use='0')]
        agd = [ x.name for x in data.domain.filter(use='1')]
    ds168d = [x.name for x in data.domain.filter(use='2')]
    webnum = len(webd)
    webtext = "\r\n".join(webd)
    agnum = len(agd)
    agtext = "\r\n".join(agd)
    ds168num = len(ds168d)
    ds168text = "\r\n".join(ds168d)
    if request.method == 'POST':
        
        return HttpResponse("OK")
    return render(request, 'automation/git_return_deploy_info.html', locals())


def gengxin_code_edit(request, uuid):
    data = gengxin_code.objects.get(pk=uuid)
    tf = gengxin_codeForm(instance=data)
    if request.method == 'POST':
        tf = gengxin_codeForm(request.POST, instance=data)
        if tf.is_valid():
            tf_data = tf.save()
            print "tf_data="+tf_data.remoteip
            fabu = fabu_update_task.delay(tf_data.uuid)
            configurate = fabu_nginxconf_task.delay(tf_data.uuid)
            resu = {'res': "OK"}
            return JsonResponse(resu, safe=False)
    return render(request, 'automation/gengxin_code_edit.html', locals())


def gengxin_code_delete(request, uuid):
    data = get_object_or_404(gengxin_code, pk=uuid)
    if data:
        data.delete()
        return HttpResponse("/deploy/gengxin_code_list/")


def changes(a,b):
   for i in xrange(0,len(a),b):
       yield  a[i:i+b]

def judge_urgent(period):
    """判断是否紧急函数"""
    now = int(time.strftime('%H%M', time.localtime(time.time())))
    period_time = period
    start_time = int(''.join(period_time.split("-")[0].split(":")))
    end_time = int(''.join(period_time.split("-")[1].split(":")))
    if end_time < start_time:
        print "error,end_time less-than start_time"
        return False
    else:
        if now > start_time and now < end_time:
            print "normal"
            return False
        else:
            print "urgent"
            return True


def deploy_time_fun(obj):
    """判断更新频率，返回ture or false"""
    if not obj.deploy_time or int(obj.deploy_time) <= 0:
        return True   #无限制则审核
    else:
        num = 0
        now = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        period_time = obj.period_time
        start_time = now +" "+ period_time.split("-")[0]
        end_time = now +" "+ period_time.split("-")[1]
        print start_time,end_time
        timeArray_start = time.strptime(start_time, "%Y-%m-%d %H:%M")
        timeArray_end = time.strptime(end_time, "%Y-%m-%d %H:%M")
        today_start = int(time.mktime(timeArray_start))
        today_end = int(time.mktime(timeArray_end))
        print today_start
        print today_end
        for i in obj.deploy.all():
            if i.execution_time:
                timeArray = time.strptime(i.execution_time, "%Y-%m-%d %H:%M:%S")
                timeStamp = int(time.mktime(timeArray))
                if today_start <= timeStamp and timeStamp <= today_end:
                    num += 1
        if num > int(obj.deploy_time):
            return True   #灰度更新太频繁达到审核次数，返回真，执行审核流程
        else:
            return False

@login_required
def gengxin_deploy_list(request):
    old_data = gengxin_code.objects.all()
    public = False
    for i in old_data:
        if judge_urgent(i.period_time):
            i.urgent = True  #如果不在期限内，此站点走紧急更新流程
            public = True   #如果有一个站点走紧急更新流程，那么public就走紧急流程
        else:
            i.urgent = False
        i.save()

    test_data = gengxin_code.objects.filter(classify="test").order_by('name')
    test_rules = []
    for i in changes(test_data,2):
        test_rules.append(i)
    try:
        rules0 = test_rules[0]
    except:
        rules0 = []
    try:
        rules1 = test_rules[1]
    except:
        rules1 = []
    try:
        rules2 = test_rules[2]
    except:
        rules2 = []
    try:
        rules3 = test_rules[3]
    except:
        rules3 = []
    huidu_data = gengxin_code.objects.filter(classify="huidu").order_by('name')
    huidu_rules = []
    for i in changes(huidu_data,2):
        huidu_rules.append(i)
    try:
        rules4 = huidu_rules[0]
    except:
        rules4 = []
    try:
        rules5 = huidu_rules[1]
    except:
        rules5 = []
    try:
        rules6 = huidu_rules[2]
    except:
        rules6 = []
    try:
        rules7 = huidu_rules[3]
    except:
        rules7 = []
    online_data = gengxin_code.objects.filter(classify="online").order_by('name')
    online_rules = []
    for i in changes(online_data,2):
        online_rules.append(i)
    try:
        rules8 = online_rules[0]
    except:
        rules8 = []
    try:
        rules9 = online_rules[1]
    except:
        rules9 = []
    try:
        rules11 = online_rules[2]
    except:
        rules11 = []
    try:
        rules12 = online_rules[3]
    except:
        rules12 = []
    return render(request,'automation/gengxin_deploy_list.html',locals())

def create_audit_data(name,audit_memo,user,classify,obj):
    audit_list = []
    audit_data = AUser.objects.get(name=classify)
    for i in audit_data.user.all(): #给紧急审核人发任务
        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
    return audit_list

def gengxin_create_deploy(request,uuid):
    if "pub_" in str(uuid):
        isurgent = uuid.split('_')[-1]
        if "huidu" in str(uuid):
            name = "灰度Public"
            env = "huidu"
        elif "online" in str(uuid):
            env = "online"
            name = "生产Public"
        else:
            env = "test"
            name = "测试Public"
        if "phone" in str(uuid):
            mname = name + "-全部手机端"
            method = "pam"
        else:
            mname = name + "-全部电脑端"
            method = "pa"
        version = website_deploy(env,'1001')
        last_version = version.last_release(method)
        if request.method == 'POST':
            memo = request.POST.get('memo')
            if not memo: memo = "无"
            public_release = request.POST.get('public_release')
            if "test" in str(uuid):
                allname = mname + "-更新"
                deploy_data = gengxin_deploy(name=allname,executive_user=request.user,status="更新中",memo=memo,siteid="all",method=method,pub_reversion=public_release)
                deploy_data.save() #任务建立后直接更新
                meimei = gengxin_update_task.delay(deploy_data.uuid,env)
            else:
                if isurgent == "urgent":
                    audit_list = []
                    audit_data = AUser.objects.get(name="website_urgent")
                    for i in audit_data.user.all(): #给紧急审核人发任务
                        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                    allname = mname + "-紧急更新"
                    deploy_data = gengxin_deploy(name=allname,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                    siteid="all",method=method,pub_reversion=public_release)
                    deploy_data.save()
                    audit_memo = {"common":memo,"env":env,"public_release":public_release,"method":method}
                    audit_res = create_audit_data(mname,audit_memo,request.user,"website_urgent",deploy_data)   #分发审核
                else:
                    audit_list = []
                    audit_data = AUser.objects.get(name="website_normal")
                    for i in audit_data.user.all(): #给紧急审核人发任务
                        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                    allname = mname + "-正常更新"
                    deploy_data = gengxin_deploy(name=allname,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                    siteid="all",method=method,pub_reversion=public_release)
                    deploy_data.save()
                    audit_memo = {"common":memo,"env":env,"public_release":public_release,"method":method}
                    audit_res = create_audit_data(mname,audit_memo,request.user,"website_normal",deploy_data)  #分发审核
            result={'res':"OK",'info':"完成public更新"}
            return JsonResponse(result,safe=False)
        return render(request,'automation/gengxin_create_public.html',locals())
    else:
        data = gengxin_code.objects.get(pk=uuid)
        if "f" in data.business.nic_name:
            phone_id = data.business.nic_name.replace('f','mf')
        else:
            phone_id = data.business.nic_name + "m"
        env = data.classify
        version = website_deploy(env,data.business.nic_name)
        last_version = version.last_release("web",isphone=data.phone_site)
        if request.method == 'POST':
            memo = request.POST.get('memo')
            if not memo: memo = "无"
            siteid = request.POST.get('siteid')
            method = request.POST.get('method')
            web_release = request.POST.get('web_release')
            pub_release = request.POST.get('public_release')
            if method == "a":
                mname = siteid+"-整站-"
            elif method == "w":
                mname = siteid + "-Web前端-"
            else:
                mname = siteid + "-Public公用库-"
            if env == "huidu":
                name = "灰度-" + mname
                if data.isurgent:
                    audit_list = []
                    audit_data = AUser.objects.get(name="website_urgent")
                    for i in audit_data.user.all(): #给紧急审核人发任务
                        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                    allname = name + "紧急更新"
                    deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                    deploy_data.save()
                    audit_memo = {"common":memo,"env":env,"public_release":pub_release,"web_release":web_release,"method":method}
                    audit_res = create_audit_data(allname,audit_memo,request.user,"website_urgent",deploy_data)  #分发审核
                else:
                    allname = name + "正常更新"
                    if data.ischeck:
                        if deploy_time_fun(data):
                            print "灰度更新次数太多，需要审核"
                            audit_list = []
                            audit_data = AUser.objects.get(name="website_normal")
                            for i in audit_data.user.all(): #给紧急审核人发任务
                                audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                            deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                            deploy_data.save()
                            audit_memo = {"common":memo,"env":env,"public_release":pub_release,"web_release":web_release,"method":method}
                            audit_res = create_audit_data(allname,audit_memo,request.user,"website_normal",deploy_data)  #分发审核
                        else:
                            print "灰度更新频率在阈值内，不需审核，直接更新"
                            deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="更新中",memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                            deploy_data.save()
                            meimei = gengxin_update_task.delay(deploy_data.uuid,env)
                    else:
                        print "灰度没有开启审核，直接更新"
                        deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="更新中",memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                        deploy_data.save()
                        meimei = gengxin_update_task.delay(deploy_data.uuid,env)
            elif env == "online":
                name = "线上-"+ mname
                if data.isurgent:
                    audit_list = []
                    audit_data = AUser.objects.get(name="website_urgent")
                    for i in audit_data.user.all(): #给紧急审核人发任务
                        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                    allname = name + "紧急更新"
                    deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                    deploy_data.save()
                    audit_memo = {"common":memo,"env":env,"public_release":pub_release,"web_release":web_release,"method":method}
                    audit_res = create_audit_data(allname,audit_memo,request.user,"website_urgent",deploy_data)  #分发审核
                else:
                    audit_list = []
                    audit_data = AUser.objects.get(name="website_normal")
                    for i in audit_data.user.all(): #给紧急审核人发任务
                        audit_list.append({"user":i.username,"isaudit":False,"ispass":False})
                    allname = name + "正常更新"
                    if data.ischeck:
                        deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="审核中",audit_status=audit_list,memo=memo,
                siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                        deploy_data.save()
                        audit_memo = {"common":memo,"env":env,"public_release":pub_release,"web_release":web_release,"method":method}
                        audit_res= create_audit_data(allname,audit_memo,request.user,"website_normal",deploy_data)  #分发审核
                    else:
                        print "线上没有开启审核，直接更新"
                        deploy_data = gengxin_deploy(name=allname,code_conf=data,executive_user=request.user,status="更新中",memo=memo,
                    siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                        deploy_data.save()
                        meimei = gengxin_update_task.delay(deploy_data.uuid,env)
            else:
                name = "测试-"+ mname
                deploy_data = gengxin_deploy(name=name,code_conf=data,executive_user=request.user,status="更新中",memo=memo,
            siteid=siteid,method=method,pub_reversion=pub_release,web_reversion=web_release)
                deploy_data.save()
                meimei = gengxin_update_task.delay(deploy_data.uuid,env)
            return JsonResponse({"res":"OK"},safe=False)
        return render(request,'automation/gengxin_create_deploy.html',locals())

@login_required
def genxin_my_deploy_task(request):
    data = gengxin_deploy.objects.filter(executive_user=request.user).order_by('-ctime')[:50]
    return render(request,'automation/gengxin_my_deploy_task.html',locals())

def gengxin_my_deploy_task_delete(request,uuid):
    print uuid
    data = gengxin_deploy.objects.get(pk=uuid)
    print data.name
    data.delete()
    return HttpResponseRedirect('/deploy/mytask/')
