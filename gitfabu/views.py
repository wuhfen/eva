#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render

from gitfabu.models import git_deploy,my_request_task,git_deploy_logs,git_deploy_audit,git_task_audit,git_coderepo,git_ops_configuration,git_code_update
from business.models import Business,DomainName,Domain_ip_pool
# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from gitfabu.tasks import git_fabu_task,git_moneyweb_deploy,git_update_task,git_update_public_task
from django.contrib.auth.decorators import login_required
import time
from api.git_api import Repo

import telegram
bot = telegram.Bot(token='333468932:AAGKPxYrLc3jkhYP68FUSnwa0DVTjR-9zmA')


def mytasknums(request):
    nums = {}
    try:
        mdata = len(my_request_task.objects.filter(initiator=request.user,isend=False,loss_efficacy=False))
    except:
        mdata = 0
    nums['myrequesttasks']=mdata
    try:
        odata = len(git_task_audit.objects.filter(auditor=request.user,isaudit=False,loss_efficacy=False))
    except:
        odata = 0
    nums['myaudittasks']=odata
    return nums

@login_required
def conf_list(request):
    data_huidu = git_deploy.objects.filter(platform="现金网",classify="huidu")
    data_test = git_deploy.objects.filter(platform="现金网",classify="test")
    data_online = git_deploy.objects.filter(platform="现金网",classify="online")
    alone = git_deploy.objects.filter(platform="单个项目")
    return render(request,'gitfabu/conf_list.html',locals())

@login_required
def version_list(request,uuid):
    data = git_deploy.objects.get(pk=uuid)
    if data.old_reversion:
        old_reversion = data.old_reversion.split('\r\n')
    else:
        old_reversion = []
    return render(request,'gitfabu/version_list.html',locals())


@login_required
def conf_add(request,env):
    print env
    errors = []

    if "money" in env:
        platform = "现金网"
        conf_domain = True
    elif "manniu" in env:
        platform = "蛮牛"
        conf_domain = True
    elif "java" in env:
        platform = "JAVA项目"
        conf_domain = False
    else:
        platform = "单个项目"
        conf_domain = False
    if "huidu" in env: 
        dname = platform + "_灰度发布"
        envir = "huidu"
        envname = "灰度"
    if "online" in env: 
        dname = platform + "_线上发布"
        envir = "online"
        envname = "生产"
    if "test" in env: 
        dname = platform + "_测试发布"
        envir = "test"
        envname = "测试"
    busi = Business.objects.filter(platform=platform)
    auditor = git_deploy_audit.objects.filter(platform=platform,classify=envir,name="发布")
    if not envir == "test": #测试环境不用审核直接发布
        if auditor:
            auditors = [i.username for i in auditor[0].user.all() if i]
        else:
            auditors = []
            errors.append("没有配置%s-%s发布审核人，请联系运维处理"% (platform,envname))
    else:
        auditors = []

    if request.method == 'POST':
        name = request.POST.get('business') #所有发布的项目使用business中的nic_name当作名称
        gg = git_deploy.objects.filter(name=name,platform=platform,classify=envir)
        if len(gg) > 0:
            errors.append("项目以存在，请联系运维处理")
        business = Business.objects.get(nic_name=name)

        #配置服务器地址，没有配置会报错，所以使用try
        try:
            if platform == "现金网" or platform == "蛮牛":
                server = git_ops_configuration.objects.filter(name="源站",platform=platform,classify=envir)[0]
            else:
                server = git_ops_configuration.objects.filter(name=name,platform=platform,classify=envir)[0]
        except IndexError:
            errors.append("没有配置-%s-%s-%s-服务器地址"% (platform,business.name,envir))

        #检测域名正确性，测试环境不会检查ag与backend域名
        if platform == "现金网" or platform == "蛮牛":
            if not request.POST.get('front'):
                errors.append("没有给出前端域名")
            else:
                f_dname = "%s-%s前端域名"% (envname,name)
                f_cname = "%s_%s.conf"% (name,envir)
                f_domainname = request.POST.get('front').split('\r\n')
            if not envir == "test":
                if not request.POST.get('ag'):
                    errors.append("没有给出ag域名")
                else:
                    a_dname = "%s-%sAG域名"% (envname,name)
                    a_cname = "%s_%s.conf"% (name,envir)
                    # a_domainname = " ".join(request.POST.get('ag').split('\r\n'))
                    a_domainname = request.POST.get('ag').split('\r\n')
                if not request.POST.get('backend'):
                    errors.append("没有给出后台域名")
                else:
                    b_dname = "%s-%s后台域名"% (envname,name)
                    b_cname = "%s.conf"% name
                    # b_domainname = " ".join(request.POST.get('backend').split('\r\n'))
                    b_domainname = request.POST.get('backend').split('\r\n')
        if errors:
            return render(request,'gitfabu/conf_add.html',locals())

        #配置git地址，如果没有找到web/1001.git类似的私有仓库，则创建保存
        money_git = "http://git.dtops.cc/"
        username = "fabu"    #写死的，以后会是一个bug
        password = "DSyunweibu110110"
        if platform == "现金网":  #注意：只有现金网和蛮牛的web项目发布时才会创建git地址，其他的单独项目和JAVA项目应该手动添加git的相关信息
            web = money_git+"web/%s.git"% name
            obj,created = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=False,title=name,defaults={'address':web,'user':username,'passwd':password},)
            php_pc,php_pc_repo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="php_pc",defaults={'address':money_git+"php/1000_public_php.git",'user':username,'passwd':password})
            php_mob,php_mob_repo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="php_mobile",defaults={'address':money_git+"php/1000m_public_php.git",'user':username,'passwd':password})
            js_pc,js_pc_repo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="js_pc",defaults={'address':money_git+"web/1000_public_js.git",'user':username,'passwd':password})
            js_mob,js_mob_repo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="js_mobile",defaults={'address':money_git+"web/1000m_public_js.git",'user':username,'passwd':password})
            configobj,configrepo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title=name+"_config",defaults={'address':money_git+"config/"+name+".git",'user':username,'passwd':password})
        elif platform == "蛮牛":
            web = money_git+"jack/%s.git"% name
            obj,created = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=False,title=name,defaults={'address':web,'user':username,'passwd':password},)
            phpobj,phprepo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="mn_php",defaults={'address':money_git+"harrisdt15f/wcphpsec.git",'user':username,'passwd':password})
            jsobj,jsrepo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="mn_js",defaults={'address':money_git+"jack/mn-web-public.git",'user':username,'passwd':password})
            configobj,configrepo = git_coderepo.objects.get_or_create(platform=platform,classify=envir,ispublic=True,title="mn_config",defaults={'address':money_git+"harrisdt15f/phpcofig.git",'user':username,'passwd':password})


        ddata,created = git_deploy.objects.get_or_create(name=name,platform=platform,classify=envir,business=business,defaults={'conf_domain':conf_domain,'server':server,'usepub':conf_domain,'isdev':True,'isops':True},)

        #保存配置域名
        if platform == "现金网" or platform == "蛮牛":
            for i in f_domainname:
                obj,created = DomainName.objects.get_or_create(name=i,use='0',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)
                if obj:
                    print "%s已存在域名%s"% (obj.classify,obj.name )
                else:
                    print "%s创建域名%s"% (created.classify,created.name)
            if not envir == "test":
                for i in a_domainname:
                    obj,created = DomainName.objects.get_or_create(name=i,use='1',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)
                for i in b_domainname:
                    obj,created = DomainName.objects.get_or_create(name=i,use='2',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)

        #分配审核任务
        task_name = "%s--%s"% (dname,name)
        memo = "%s,%s环境,%s发布"% (platform,envname,name)
        mydata = my_request_task(name=task_name,table_name="git_deploy",uuid=ddata.id,initiator=request.user,memo=memo,status="审核中")
        mydata.save()
        if envir == 'test':  #测试环境直接发布，其他环境需要分发审核任务
            mydata.status = "发布中"
            mydata.save()
            reslut = git_fabu_task.delay(ddata.id,mydata.id)
        else:
            for i in auditor[0].user.all():
                # if i.username == "lookback":
                #     bot.sendMessage(chat_id='228902627', text="有审核任务")
                task_data = git_task_audit(request_task=mydata,auditor=i)
                task_data.save()

    return render(request,'gitfabu/conf_add.html',locals())

@login_required
def my_request_task_list(request):
    if request.user.username == "wuhf":
        data = my_request_task.objects.filter(isend=False,loss_efficacy=False).order_by('-create_date')
    else:
        data = my_request_task.objects.filter(initiator=request.user).order_by('-create_date')
    return render(request,'gitfabu/my_request_task.html',locals())

@login_required
def others_request_task_list(request):
    if request.user.username == "wuhf":
        data = []
        ll = []
        sdata = my_request_task.objects.filter(isend=False,loss_efficacy=False)
        for i in sdata:
            for j in i.reqt.all():
                data.append(j)
    else:
        data = git_task_audit.objects.filter(auditor=request.user).order_by('-create_date')
    return render(request,'gitfabu/others_request_task.html',locals())

@login_required
def cancel_my_task(request,uuid):
    data = my_request_task.objects.get(id=uuid)
    data.loss_efficacy=True
    data.status="已停止"
    data.save()  #停止此次申请任务
    data.reqt.all().update(loss_efficacy=True) #停止相关的审核任务

    eval(data.table_name).objects.get(pk=data.uuid).delete() #删除此次申请发布的项目信息，自动创建的gitrepo没有被删除
    return JsonResponse({'res':"已经终止申请"},safe=False)

@login_required
def my_task_details(request,uuid):
    data = my_request_task.objects.get(id=uuid)
    others_data = data.reqt.all().order_by('audit_time')
    if data.loss_efficacy:
        return render(request,'gitfabu/my_task_details.html',locals())
    if data.table_name == "git_deploy":
        classify = "fabu"
        df = eval(data.table_name).objects.get(pk=data.uuid)
        dflog = df.deploy_logs.filter(name="发布")
        gitprivate = git_coderepo.objects.filter(platform=df.platform,classify=df.classify,ispublic=False,title=df.name)
        
        auditors = git_deploy_audit.objects.filter(platform=df.platform,classify=df.classify,name="发布")
        if df.platform == "现金网" or df.platform == "蛮牛":
            fabu_details = True
            domains = df.business.domain.filter(classify=df.classify)
            gitpublic = git_coderepo.objects.filter(platform=df.platform,classify=df.classify,ispublic=True)
            servers = git_ops_configuration.objects.filter(platform=df.platform,classify=df.classify,name="源站")
        else:
            fabu_details = False
            domains = None
            servers = git_ops_configuration.objects.filter(platform=df.platform,classify=df.classify,name=df.name)
    else:
        classify = "gengxin"
        df = eval(data.table_name).objects.get(pk=data.uuid)
        deploy_data = df.code_conf
        if deploy_data: #如果有项目外键
            dflog = deploy_data.deploy_logs.filter(name="更新",update=df.id)
            auditors = git_deploy_audit.objects.filter(platform=deploy_data.platform,classify=deploy_data.classify,name="更新",isurgent=df.isurgent)
            if df.method == "php_pc" or df.method == "php_mobile" or df.method == "js_pc" or df.method == "js_mobile":
                name = "%s-电脑端更新"% df.method
                repo = git_coderepo.objects.get(platform="现金网",classify=deploy_data.classify,title=df.method,ispublic=True).address
            elif df.method == "php" or df.method == "config" or df.method == "js":
                name = "蛮牛%s-公共代码更新"% df.method
                repo = git_coderepo.objects.get(platform="蛮牛",classify=deploy_data.classify,title="mn_"+df.method,ispublic=True).address
            else:
                name = "%s-更新"% deploy_data.name
                repo = git_coderepo.objects.get(platform=deploy_data.platform,classify=deploy_data.classify,ispublic=False,title=deploy_data.name).address
            version = df.version
            branch = df.branch
            version_details = df.details
        else: #没有项目外键，判断属于公共代码全部更新
            dflog = git_deploy_logs.objects.filter(name="更新",update=df.id)
            if "huidu" in df.name: env = "huidu"
            if "online" in df.name: env = "online"
            if "test" in df.name: env= "test"
            if "现金网" in df.name: platform = "现金网"
            if "蛮牛" in df.name: platform = "蛮牛"
            if env == "test":
                auditors = None
            else:
                auditors = git_deploy_audit.objects.filter(platform=platform,classify=env,name="更新",isurgent=df.isurgent)
            if df.method == "php_pc" or df.method == "php_mobile" or df.method == "js_pc" or df.method == "js_mobile":
                repo = git_coderepo.objects.get(platform=platform,classify=env,title=df.method,ispublic=True).address
                name = "%s-电脑端更新"% df.method
            elif df.method == "php" or df.method == "config" or df.method == "js":
                repo = git_coderepo.objects.get(platform=platform,classify=env,title="mn_"+df.method,ispublic=True).address
                name = "蛮牛%s-公共代码更新"% df.method
            version = df.version
            branch = df.branch
            version_details = df.details
    return render(request,'gitfabu/my_task_details.html',locals())

@login_required
def audit_my_task(request,uuid):
    """审核任务，分发布与更新的审核后续处理"""
    data = git_task_audit.objects.get(pk=uuid)
    df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
    print "项目id：%s任务id：%s"% (df.id,data.request_task.id)
    if request.method == 'POST':
        ispass = request.POST.get('ispass')
        if ispass == "yes":
            ok = True
        else:
            ok = False
        postil = request.POST.get('postil')
        data.isaudit = True
        data.ispass = ok 
        data.postil = postil
        data.save()
        alldata = data.request_task.reqt.all()
        if False not in [i.ispass for i in alldata]:
            print "所有审核已通过，开始更新发布"
            print [i.ispass for i in alldata]
            data.request_task.status="通过审核，更新中"
            data.request_task.save()
            df.isaudit= True
            df.save()
            print "项目id：%s任务id：%s"% (df.id,data.request_task.id)
            if data.request_task.table_name == "git_deploy":
                reslut = git_fabu_task.delay(df.id,data.request_task.id)
            else:
                if df.code_conf:
                    reslut = git_update_task.delay(data.request_task.uuid,data.request_task.id)
                else:
                    if "现金网" in df.name: platform="现金网"
                    if "蛮牛" in df.name: platform="蛮牛"
                    reslut = git_update_public_task.delay(data.request_task.uuid,data.request_task.id,platform=platform)
        else:
            print "尚有审核未通过"
        return JsonResponse({'res':"OK"},safe=False)

    return render(request,'gitfabu/audit_my_task.html',locals())

@login_required
def web_update_code(request,uuid):
    """一个更新任务添加，现获取所有的分支信息，线上环境只有master分支展示"""
    data = git_deploy.objects.get(pk=uuid)

    WaitTask = data.deploy_update.filter(islog=False)
    if not WaitTask: WaitTask = git_code_update.objects.filter(name__contains=data.platform,islog=False)

    if data.old_reversion:
        old_reversion = data.old_reversion.split('\r\n')[0:5]
    else:
        old_reversion = []


    if request.method == 'GET':
        if data.platform == "现金网" or data.platform == "蛮牛":
            all_branch = ['master']
            web_commits = []
        else:
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what='web')
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what='web')

    if request.method == 'POST':
        #先判断这个站是否被锁住了，没有锁就继续
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')
        #获取当前版本号,组成新版本信息
        old_data = git_code_update.objects.get(code_conf=data,islog=True,isuse=True)
        web_branches = old_data.web_branches
        web_release = old_data.web_release
        php_pc_branches = old_data.php_pc_branches
        php_pc_release = old_data.php_pc_release
        php_mobile_branches = old_data.php_mobile_branches
        php_moblie_release = old_data.php_moblie_release
        js_pc_branches = old_data.js_pc_branches
        js_pc_release = old_data.js_pc_release
        js_mobile_branches = old_data.js_mobile_branches
        js_mobile_release = old_data.js_mobile_release
        config_branches = old_data.config_branches
        config_release = old_data.config_release
        if method == 'web':
            web_release = release[0:7]
            web_branches = branch
        elif method == "php_pc" or method == "php":
            php_pc_release = release[0:7]
            php_pc_branches = branch
        elif method == "php_mobile":
            php_moblie_release = release[0:7]
            php_mobile_branches = branch
        elif method == "js_pc" or method == "js":
            js_pc_release = release[0:7]
            js_pc_branches = branch
        elif method == "js_mobile":
            js_mobile_release = release[0:7]
            js_mobile_branches = branch
        else:
            config_branches = branch
            config_release = release[0:7]
        #判断是否紧急
        if data.classify == 'huidu' or data.classify == 'online':
            normal_auditor = git_deploy_audit.objects.get(platform=data.platform,classify=data.classify,isurgent=False,name="更新") #正常审核人
            php_auditor = git_deploy_audit.objects.get(platform=data.platform,classify=data.classify,isurgent=False,name="php更新") #PHP代码正常审核人
            urgent_auditor = git_deploy_audit.objects.get(platform=data.platform,classify=data.classify,isurgent=True,name="更新") #紧急审核人
            c = int(normal_auditor.start_time.replace(":",""))
            d = int(normal_auditor.end_time.replace(":",""))
            now = time.strftime('%H:%M',time.localtime(time.time()))
            e = int(now.replace(":",""))
            if c <= e and d >= e:
                print("normal不紧急")
                if method == "php_pc" or method == "php_mobile" or method == "php" or method == "config":
                    auditor = php_auditor
                else:
                    auditor = normal_auditor
                print auditor.name
                isurgent = False
                name = data.platform+"-"+data.classify+"-"+data.name+"-"+method+"-更新"
            else:
                print("urgent紧急更新")
                auditor = urgent_auditor
                isurgent = True
                name = data.platform+"-"+data.classify+"-"+data.name+"-"+method+"-紧急更新"
        else:
            isurgent = False
            name = data.platform+"-"+data.classify+"-"+data.name+"-"+method+"-更新"
        #保存更新版本信息
        updata = git_code_update(name=name,code_conf=data,method=method,version=release[0:7],branch=branch,web_release=web_release,php_pc_release=php_pc_release,
            php_moblie_release=php_moblie_release,js_pc_release=js_pc_release,js_mobile_release=js_mobile_release,config_release=config_release,
            web_branches=web_branches,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,
            js_mobile_branches=js_mobile_branches,config_branches=config_branches,memo=memo,details=release,isurgent=isurgent,last_version=data.now_reversion)
        updata.save()
        #给此项目上锁
        data.islock = True
        data.save()
        #创建更新申请
        mydata = my_request_task(name=name,table_name="git_code_update",uuid=updata.id,memo=memo,initiator=request.user,status="审核中")
        mydata.save()
        #创建审核，测试环境不需要审核
        if data.name == "1029": #现金网1029特例
            mydata.status="通过审核，更新中"
            mydata.save()
            updata.isaudit = True
            updata.save()
            reslut = git_update_task.delay(updata.id,mydata.id)
        else:
            if data.classify == 'huidu' or data.classify == 'online':
                for i in auditor.user.all():
                    # if i.username == "wuhf":
                    #     bot.sendMessage(chat_id='229344728', text="有审核任务")
                    # if i.username == "lookback":
                    #     bot.sendMessage(chat_id='228902627', text="有审核任务")
                    #     bot.sendMessage(chat_id='228902627', text="任务ID: %s,名称：%s"% (task_data.id,task_name))
                    task_data = git_task_audit(request_task=mydata,auditor=i)
                    task_data.save()
            else:
                mydata.status="通过审核，更新中"
                mydata.save()
                updata.isaudit = True
                updata.save()
                reslut = git_update_task.delay(updata.id,mydata.id)
        return JsonResponse({'res':"OK"},safe=False)

    return render(request,'gitfabu/web_update_code.html',locals())

def public_update_code(request,env):
    """公共代码更新"""
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"

    if "money" in env:
        base_export_dir = "/data/moneyweb/" + classify + "/export/php_pc"
        platform = "现金网"
    elif "manniu" in env:
        base_export_dir = "/data/manniuweb/" + classify + "/export/mn_php"
        platform = "蛮牛"

    gitrepo = Repo(base_export_dir)
    all_branch = gitrepo.git_all_branch()
    commit = gitrepo.show_commit()
    WaitTask = git_deploy.objects.filter(platform=platform,classify=classify,islock=True) #如果某个站有锁，则无法申请全站更新

    if request.method == 'POST':
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')

        #判断是否紧急
        if classify == 'huidu' or classify == 'online':
            normal_auditor = git_deploy_audit.objects.get(platform=platform,classify=classify,isurgent=False,name="更新") #正常审核人
            php_auditor = git_deploy_audit.objects.get(platform=platform,classify=classify,isurgent=False,name="php更新") #PHP代码正常审核人
            urgent_auditor = git_deploy_audit.objects.get(platform=platform,classify=classify,isurgent=True,name="更新") #紧急审核人
            c = int(normal_auditor.start_time.replace(":",""))
            d = int(normal_auditor.end_time.replace(":",""))
            now = time.strftime('%H:%M',time.localtime(time.time()))
            e = int(now.replace(":",""))
            if c <= e and d >= e:
                if method == "php_pc" or method == "php_mobile" or method == "php" or method == "config":
                    auditor = php_auditor
                else:
                    auditor = normal_auditor
                print auditor.name
                isurgent = False
                name = platform +"-"+classify+"-公共代码-"+method+"-更新"
            else:
                auditor = urgent_auditor
                isurgent = True
                name = platform +"-"+classify+"-公共代码-"+method+"-紧急更新"
        else:
            isurgent = False
            name = platform +"-"+classify+"-公共代码-"+method+"-更新"
        #保存更新任务
        updata = git_code_update(name=name,method=method,version=release[0:7],branch=branch,memo=memo,details=release,isurgent=isurgent)
        updata.save()
        #创建更新申请
        mydata = my_request_task(name=name,table_name="git_code_update",uuid=updata.id,memo=memo,initiator=request.user,status="审核中")
        mydata.save()
        git_deploy.objects.filter(platform=platform,classify=classify,islog=True,usepub=True).update(islock=True) #迁移的时候别忘记把所有的项目usepub项更新为真
        #创建审核
        if classify == "test":
            mydata.status="通过审核，更新中"
            mydata.save()
            updata.isaudit = True
            updata.save()
            reslut = git_update_public_task.delay(updata.id,mydata.id,platform=platform)
        else:
            for i in auditor.user.all():
                task_data = git_task_audit(request_task=mydata,auditor=i)
                task_data.save()
        return JsonResponse({'res':"OK"},safe=False)
    return render(request,'gitfabu/public_update_code.html',locals())

def ops_confguration(request):
    """配置页面，包含审核人，线上服务器，公用public地址"""
    repo_data = git_coderepo.objects.filter(platform="现金网",ispublic=True)
    audit_data = git_deploy_audit.objects.filter(platform="现金网")
    ops_data = git_ops_configuration.objects.filter(platform="现金网")
    return render(request,'gitfabu/ops_confguration.html',locals())

def batch_change(request,uuid):
    """切换分支并获取最新的版本号10条"""
    env = request.GET.get('env')
    method = request.GET.get('method')
    branch = request.GET.get('branch')
    if env == "moneyweb":
        print "现金网查询版本号"
        if not method:
            res = {'res':"OK",'branches':[],"commit":[]}
            return JsonResponse(res,safe=False)
        if branch:
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what=method,branch=branch)
            res = {'res':"OK","commit":web_commits}
        else:
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what=method)
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what=method)
            res = {'res':"OK",'branches':all_branch,"commit":web_commits}
    else:
        print "蛮牛网查询版本号"
        if not method:
            res = {'res':"OK",'branches':[],"commit":[]}
            return JsonResponse(res,safe=False)
        if branch:
            web_commits = manniu_web_deploy(uuid).branch_checkout(what=method,branch=branch)
            res = {'res':"OK","commit":web_commits}
        else:
            data = manniu_web_deploy(uuid)
            all_branch = data.deploy_all_branch(what=method)
            web_commits = manniu_web_deploy(uuid).branch_checkout(what=method)
            res = {'res':"OK",'branches':all_branch,"commit":web_commits}
    print res
    return JsonResponse(res,safe=False)

def public_branch_change(request):
    name = request.GET.get('name')
    env = request.GET.get('env')
    branch = request.GET.get('branch')

    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"

    if "money" in env:
        base_dir = "/data/moneyweb/" + classify + "/export/"
        platform = "现金网"
    elif "manniu" in env:
        base_dir = "/data/manniuweb/" + classify + "/export/"
        platform = "蛮牛"


    if name == 'php_pc' or name == 'php_mobile' or name == 'js_pc' or name == 'js_mobile':
        path = base_dir + name
    elif name == 'php' or name == 'js' or name == 'config':
        path = base_dir + "mn_"+name

    gitrepo = Repo(path)
    if branch:
        gitrepo.git_checkout(branch)
        gitrepo.git_pull()
        commit = gitrepo.show_commit()
        res = {'res':"OK","commit":commit}
    else:
        gitrepo.git_checkout('master')
        gitrepo.git_pull()
        all_branch = gitrepo.git_all_branch()
        commit = gitrepo.show_commit()
        res = {'res':"OK",'branches':all_branch,"commit":commit}
    return JsonResponse(res,safe=False)

@login_required
def manniu_list(request):
    data = git_deploy.objects.filter(platform="JAVA项目") #蛮牛java组件项目
    data_huidu = git_deploy.objects.filter(platform="蛮牛",classify="huidu")
    data_online = git_deploy.objects.filter(platform="蛮牛",classify="online")
    return render(request,'gitfabu/manniu_list.html',locals())
