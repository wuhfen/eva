#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render

from gitfabu.models import git_deploy,my_request_task,git_deploy_logs,git_deploy_audit,git_task_audit,git_coderepo,git_ops_configuration,git_website_domainname,git_code_update
from business.models import Business
# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from gitfabu.tasks import git_fabu_task,git_moneyweb_deploy,git_update_task,git_update_public_task,commit_details_task
from django.contrib.auth.decorators import login_required
import time
from api.git_api import Repo

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
    data_huidu = git_deploy.objects.filter(classify="huidu")
    
    data_test = git_deploy.objects.filter(classify="test")
    data_online = git_deploy.objects.filter(classify="online")
    return render(request,'gitfabu/conf_list.html',locals())

@login_required
def conf_add(request,env):
    print env
    errors = []
    if "money" in env:
        platform = "现金网"
        conf_domain=True
    if "manniu" in env:
        platform="蛮牛"
        conf_domain=True
    if "huidu" in env: 
        dname = platform + "---->>灰度发布"
        envir = "huidu"
        envname = "灰度"
    if "online" in env: 
        dname = platform + "---->>线上发布"
        envir = "online"
        envname = "生产"
    if "test" in env: 
        dname = platform + "---->>测试发布"
        envir = "test"
        envname = "测试"
    money_git = "http://git.dtops.cc/"
    manniu_git = "http://git.dtops.cc/"
    busi = Business.objects.filter(platform=platform)
    auditor = git_deploy_audit.objects.filter(platform=platform,classify=envir,name="发布")
    if not envir == "test":
        if auditor:
            auditors = [i.username for i in auditor[0].user.all() if i]
        else:
            auditors = []
            errors.append("没有配置%s-%s发布审核人，请联系运维处理"% (platform,envname))
    else:
        auditors = []
    if request.method == 'POST':
        name = request.POST.get('business')
        gg = git_deploy.objects.filter(name=name,platform=platform,classify=envir)
        if len(gg) > 0:
            errors.append("项目以存在，请联系运维处理")

        business = Business.objects.get(nic_name=name)
        #配置git地址
        if platform == "现金网":
            username = "fabu"
            password = "DSyunweibu110110"
            web = money_git+"web/%s.git"% name
            webrepo = git_coderepo.objects.filter(platform=platform,classify=envir,ispublic=False,title=name)
            if  len(webrepo) == 0:
                dd = git_coderepo(platform=platform,classify=envir,ispublic=False,title=name,address=web,user=username,passwd=password)
                dd.save()
        else:
            pass
        #配置服务器地址
        try:
            server = git_ops_configuration.objects.filter(name="源站",platform=platform,classify=envir)[0]
        except IndexError:
            ll = "运维没有配置-%s-%s-服务器地址"% (platform,envir)
            errors.append(ll)
        #检测域名正确性
        if not request.POST.get('front'): 
            errors.append("没有给出前端域名")
        else:
            f_dname = "%s-%s前端域名"% (envname,name)
            f_cname = "%s_%s.conf"% (name,envir)
            f_domainname = " ".join(request.POST.get('front').split('\r\n'))
        if not envir == "test":
            if not request.POST.get('ag'): 
                errors.append("没有给出ag域名")
            else:
                a_dname = "%s-%sAG域名"% (envname,name)
                a_cname = "%s_%s.conf"% (name,envir)
                a_domainname = " ".join(request.POST.get('ag').split('\r\n'))
            if not request.POST.get('backend'): 
                errors.append("没有给出后台域名")
            else:
                b_dname = "%s-%s后台域名"% (envname,name)
                b_cname = "%s.conf"% name
                b_domainname = " ".join(request.POST.get('backend').split('\r\n'))
        if errors:
            return render(request,'gitfabu/conf_add.html',locals())


        ddata = git_deploy(name=name,platform=platform,classify=envir,business=business,conf_domain=conf_domain,server=server,isdev=True,isops=True)
        ddata.save()

        #配置域名
        domain_f = git_website_domainname(name=f_dname,conf_file_name=f_cname,domainname=f_domainname,git_deploy=ddata)
        domain_f.save()
        if not envir == "test":
            domain_a = git_website_domainname(name=a_dname,conf_file_name=a_cname,domainname=a_domainname,git_deploy=ddata)
            domain_a.save()
            domain_b = git_website_domainname(name=b_dname,conf_file_name=b_cname,domainname=b_domainname,git_deploy=ddata)
            domain_b.save()
        #分配审核任务
        task_name = "%s--%s"% (dname,name)
        memo = "%s,%s环境,新站%s发布"% (platform,envname,name)
        table_name = "git_deploy"
        uuid = ddata.id 
        initiator = request.user 
        mydata = my_request_task(name=task_name,table_name=table_name,uuid=uuid,initiator=initiator,memo=memo,status="审核中")
        mydata.save()
        if envir == 'test':  #测试环境直接发布，其他环境需要分发审核任务
            mydata.status = "发布中"
            mydata.save()
            reslut = git_fabu_task.delay(uuid,mydata.id)
        else:
            for i in auditor[0].user.all():
                task_data = git_task_audit(request_task=mydata,auditor=i)
                task_data.save()
    return render(request,'gitfabu/conf_add.html',locals())

@login_required
def my_request_task_list(request):
    data = my_request_task.objects.filter(initiator=request.user).order_by('-create_date')
    for i in data:
        print i.name
    return render(request,'gitfabu/my_request_task.html',locals())

@login_required
def others_request_task_list(request):
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
        if df.platform == "现金网":
            gitpublic = git_coderepo.objects.filter(platform="现金网",ispublic=True)
            gitprivate = git_coderepo.objects.filter(platform="现金网",classify=df.classify,ispublic=False,title=df.name)
            domains = df.deploy_domain.all()
            servers = git_ops_configuration.objects.filter(platform="现金网",classify=df.classify)
            auditors = git_deploy_audit.objects.filter(platform="现金网",classify=df.classify,name="发布")
    else: 
        classify = "gengxin"
        df = eval(data.table_name).objects.get(pk=data.uuid)
        deploy_data = df.code_conf
        if deploy_data: #如果有项目外键
            dflog = deploy_data.deploy_logs.filter(name="更新",update=df.id)
            if deploy_data.platform == "现金网":
                auditors = git_deploy_audit.objects.filter(platform="现金网",classify=deploy_data.classify,name="更新",isurgent=df.isurgent)
                gitrepo = git_moneyweb_deploy(deploy_data.id)
                if df.method == "web":
                    name = "web更新"
                    repo = git_coderepo.objects.get(platform="现金网",classify=deploy_data.classify,ispublic=False,title=deploy_data.name).address
                    version = df.web_release
                    branch = df.web_branches
                    # version_details = gitrepo.commit_details(what='web',reversion=version).split('\n')
                    version_details = df.details
                elif df.method == "php_pc":
                    name = "PHP电脑端更新"
                    repo = git_coderepo.objects.get(platform="现金网",title="php_pc",ispublic=True).address
                    version = df.php_pc_release
                    branch = df.php_pc_branches
                    # version_details = gitrepo.commit_details(what='php_pc',reversion=version).split('\n')
                    version_details = df.details
                elif df.method == "php_mobile":
                    name = "PHP手机端更新"
                    repo = git_coderepo.objects.get(platform="现金网",title="php_mobile",ispublic=True).address
                    version = df.php_moblie_release
                    branch = df.php_mobile_branches
                    # version_details = gitrepo.commit_details(what='php_mobile',reversion=version).split('\n')
                    version_details = df.details
                elif df.method == "js_pc":
                    name = "JS电脑端更新"
                    repo = git_coderepo.objects.get(platform="现金网",title="js_pc",ispublic=True).address
                    version = df.js_pc_release
                    branch = df.js_pc_branches
                    # version_details = gitrepo.commit_details(what='js_pc',reversion=version).split('\n')
                    version_details = df.details
                else:
                    name = "JS手机端更新"
                    repo = git_coderepo.objects.get(platform="现金网",title="js_mobile",ispublic=True).address
                    version = df.js_mobile_release
                    branch = df.js_mobile_branches
                    # version_details = gitrepo.commit_details(what='js_mobile',reversion=version).split('\n')
                    version_details = df.details
        else: #没有项目外键，判断属于公共代码全部更新
            dflog = git_deploy_logs.objects.filter(name="更新",update=df.id)
            if "huidu" in df.name:
                env = "huidu"
            elif "online" in df.name:
                env = "online"
            else:
                env= "test"
            if env == "test":
                auditors = None
            else:
                auditors = git_deploy_audit.objects.filter(platform="现金网",classify=env,name="更新",isurgent=df.isurgent)
            gitrepo = git_moneyweb_deploy(git_deploy.objects.filter(platform="现金网",classify=env,islog=True)[0].id)
            repo = git_coderepo.objects.get(platform="现金网",title=df.method,ispublic=True).address
            if df.method == "php_pc":
                version = df.php_pc_release
                branch = df.php_pc_branches
                name = "PHP电脑端更新"
            elif df.method == "php_mobile":
                version = df.php_moblie_release
                branch = df.php_mobile_branches
                name = "PHP手机端更新"
            elif df.method == "js_pc":
                version = df.js_pc_release
                branch = df.js_pc_branches
                name = "JS电脑端更新"
            else:
                version = df.js_mobile_release
                branch = df.js_mobile_branches
                name = "JS手机端更新"
            try:
                version_details = df.details
                # version_details = gitrepo.commit_details(what=df.method,reversion=version).split('\n')
            except:
                version_details = ["没有版本号信息，请确认是否合法！"]



    return render(request,'gitfabu/my_task_details.html',locals())

@login_required
def audit_my_task(request,uuid):
    """审核任务，分发布与更新的审核后续处理"""
    data = git_task_audit.objects.get(pk=uuid)
    df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
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
            if data.request_task.table_name == "git_deploy":
                reslut = git_fabu_task.delay(data.request_task.uuid,data.request_task.id)
            else:
                if df.code_conf:
                    reslut = git_update_task.delay(data.request_task.uuid,data.request_task.id)
                else:
                    reslut = git_update_public_task.delay(data.request_task.uuid,data.request_task.id)
        else:
            print "尚有审核未通过"
        return JsonResponse({'res':"OK"},safe=False)

    return render(request,'gitfabu/audit_my_task.html',locals())

@login_required
def web_update_code(request,uuid):
    """一个更新任务添加，现获取所有的分支信息，线上环境只有master分支展示"""
    data = git_deploy.objects.get(pk=uuid)
    try:
        old_reversion = data.old_reversion.split('\r\n')[-5:5]
        old_reversion.reverse()

        old_reversion = "\r\n".join(old_reversion)
    except:
        old_reversion = "Nothing"
    try:
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
        if request.method == 'GET':
            # all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what='web')
            # web_commits = git_moneyweb_deploy(uuid).branch_checkout(what='web',branch=old_data.web_branches)
            all_branch = ['master']
            web_commits = []
    except:
        if data.classify == 'test':
            web_branches = 'test'
            php_pc_branches = 'test'
            php_mobile_branches = 'test'
            js_pc_branches = 'test'
            js_mobile_branches = 'test'
            web_release = git_moneyweb_deploy(uuid).branch_checkout(what='web',branch='test')[0]
            php_pc_release = git_moneyweb_deploy(uuid).branch_checkout(what='php_pc',branch='test')[0]
            php_moblie_release = git_moneyweb_deploy(uuid).branch_checkout(what='php_moblie',branch='test')[0]
            js_pc_release = git_moneyweb_deploy(uuid).branch_checkout(what='js_pc',branch='test')[0]
            js_mobile_release = git_moneyweb_deploy(uuid).branch_checkout(what='js_mobile',branch='test')[0]
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what='web')
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what='web',branch='test')
        else:
            web_branches = 'master'
            php_pc_branches = 'master'
            php_mobile_branches = 'master'
            js_pc_branches = 'master'
            js_mobile_branches = 'master'
            web_release = git_moneyweb_deploy(uuid).branch_checkout(what='web')[0]
            php_pc_release = git_moneyweb_deploy(uuid).branch_checkout(what='php_pc')[0]
            php_moblie_release = git_moneyweb_deploy(uuid).branch_checkout(what='php_moblie')[0]
            js_pc_release = git_moneyweb_deploy(uuid).branch_checkout(what='js_pc')[0]
            js_mobile_release = git_moneyweb_deploy(uuid).branch_checkout(what='js_mobile')[0]
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what='web')
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what='web')

    if request.method == 'POST':
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')
        #获取当前版本号,组成新版本信息
        if method == 'web':
            web_release = release
            web_branches = branch
        elif method == "php_pc":
            php_pc_release = release
            php_pc_branches = branch
        elif method == "php_moblie":
            php_moblie_release = release
            php_mobile_branches = branch
        elif method == "js_pc":
            js_pc_release = release
            js_pc_branches = branch
        elif method == "js_mobile":
            js_mobile_release = release
            js_mobile_branches = branch
        else:
            pass
        #判断是否紧急
        if data.classify == 'huidu' or data.classify == 'online':
            normal_auditor = git_deploy_audit.objects.get(platform=data.platform,classify=data.classify,isurgent=False,name="更新") #正常审核人
            urgent_auditor = git_deploy_audit.objects.get(platform=data.platform,classify=data.classify,isurgent=True,name="更新") #紧急审核人
            c = int(normal_auditor.start_time.replace(":",""))
            d = int(normal_auditor.end_time.replace(":",""))
            now = time.strftime('%H:%M:%S',time.localtime(time.time()))
            e = int(now.replace(":",""))
            if c <= e and d >= e:
                print("normal不紧急")
                auditor = normal_auditor
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
        updata = git_code_update(name=name,code_conf=data,method=method,web_release=web_release,php_pc_release=php_pc_release,
            php_moblie_release=php_moblie_release,js_pc_release=js_pc_release,js_mobile_release=js_mobile_release,
            web_branches=web_branches,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,
            js_mobile_branches=js_mobile_branches,memo=memo,isurgent=isurgent)
        updata.save()
        commit_details_task.delay(updata.id) #记录版本详情
        #创建更新申请
        table_name = "git_code_update"
        uuid = updata.id
        initiator = request.user 
        mydata = my_request_task(name=name,table_name=table_name,uuid=uuid,memo=memo,initiator=initiator,status="审核中")
        mydata.save()
        #创建审核，测试环境不需要审核
        if data.classify == 'huidu' or data.classify == 'online':
            for i in auditor.user.all():
                task_data = git_task_audit(request_task=mydata,auditor=i)
                task_data.save()
        else:
            mydata.status="通过审核，更新中"
            mydata.save()
            updata.isaudit = True
            updata.save()
            reslut = git_update_task.delay(uuid,mydata.id)
        return JsonResponse({'res':"OK"},safe=False)

    return render(request,'gitfabu/web_update_code.html',locals())

def public_update_code(request,env):
    """现金网公共代码更新"""
    base_export_dir = "/data/moneyweb/" + env + "/export/php_pc"
    gitrepo = Repo(base_export_dir)
    all_branch = gitrepo.git_all_branch()
    commit = gitrepo.show_commit()
    if request.method == 'POST':
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')
        #设置版本号
        php_pc_release = ""
        php_moblie_release = ""
        js_pc_release = ""
        js_mobile_release = ""
        php_pc_branches = ""
        php_mobile_branches = ""
        js_pc_branches = ""
        js_mobile_branches = ""
        if method == 'php_pc':
            php_pc_release = release
            php_pc_branches = branch
        elif method == "php_moblie":
            php_moblie_release = release
            php_mobile_branches = branch
        elif method == "js_pc":
            js_pc_release = release
            js_pc_branches = branch
        elif method == "js_mobile":
            js_mobile_release = release
            js_mobile_branches = branch
        else:
            pass
        #判断是否紧急
        if env == 'huidu' or env == 'online':
            normal_auditor = git_deploy_audit.objects.get(platform="现金网",classify=env,isurgent=False,name="更新") #正常审核人
            urgent_auditor = git_deploy_audit.objects.get(platform="现金网",classify=env,isurgent=True,name="更新") #紧急审核人
            c = int(normal_auditor.start_time.replace(":",""))
            d = int(normal_auditor.end_time.replace(":",""))
            now = time.strftime('%H:%M:%S',time.localtime(time.time()))
            e = int(now.replace(":",""))
            if c <= e and d >= e:
                auditor = normal_auditor
                isurgent = False
                name = "现金网-"+env+"-公共代码-"+method+"-更新"
            else:
                auditor = urgent_auditor
                isurgent = True
                name = "现金网-"+env+"-公共代码-"+method+"-紧急更新"
        else:
            isurgent = False
            name = "现金网-"+env+"-公共代码-"+method+"-更新"
        #保存更新任务
        updata = git_code_update(name=name,method=method,php_pc_release=php_pc_release,php_moblie_release=php_moblie_release,
            js_pc_release=js_pc_release,js_mobile_release=js_mobile_release,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,
            js_mobile_branches=js_mobile_branches,memo=memo,isurgent=isurgent)
        updata.save()
        commit_details_task.delay(updata.id,env=env) #记录版本详情
        #创建更新申请
        table_name = "git_code_update"
        uuid = updata.id
        initiator = request.user 
        mydata = my_request_task(name=name,table_name=table_name,uuid=uuid,memo=memo,initiator=initiator,status="审核中")
        mydata.save()
        #创建审核
        if env == "test":
            mydata.status="通过审核，更新中"
            mydata.save()
            updata.isaudit = True
            updata.save()
            reslut = git_update_public_task.delay(updata.id,mydata.id)
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
    method = request.GET.get('method')
    branch = request.GET.get('branch')
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
    print res
    return JsonResponse(res,safe=False)

def public_branch_change(request):
    name = request.GET.get('name')
    env = request.GET.get('env')
    branch = request.GET.get('branch')
    print branch
    base_dir = "/data/moneyweb/" + env + "/export/"
    if name == 'php_pc':
        path = base_dir + "php_pc"
    elif name == 'php_mobile':
        path = base_dir + "php_mobile"
    elif name == 'js_pc':
        path = base_dir + "js_pc"
    elif name == 'js_mobile':
        path = base_dir + "js_mobile"
    else:
        pass
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