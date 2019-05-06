#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render

from gitfabu.models import git_deploy, my_request_task, git_deploy_logs, git_deploy_audit, git_task_audit, git_coderepo, git_ops_configuration, git_code_update
from business.models import Business, DomainName
from assets.models import Server
import subprocess
from audit.models import sql_apply, sql_conf
from accounts.models import department_Mode
from gitfabu.forms import git_deploy_audit_from
# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from gitfabu.tasks import git_fabu_task, git_moneyweb_deploy, git_update_task, git_update_public_task, send_message_task, git_batch_update_task
from django.contrib.auth.decorators import login_required
import time
from api.git_api import Repo
from gitfabu.audit_api import task_distributing, check_group_audit, onekey_access, get_the_group_audit_result
import telegram
import pdb
import uuid
from collections import OrderedDict  # 引入有序字典
bot = telegram.Bot(token='460040810:AAG4NYR9TMwcscrxg0uXLJdsDlP3a6XohJo')


def mytasknums(request):
    nums = {}
    try:
        mdata = len(my_request_task.objects.filter(initiator=request.user, isend=False, loss_efficacy=False))
    except:
        mdata = 0
    nums['myrequesttasks'] = mdata
    try:
        #odata = len(git_task_audit.objects.filter(auditor=request.user,isaudit=False,loss_efficacy=False))
        data = git_task_audit.objects.filter(auditor=request.user, isaudit=False, loss_efficacy=False)
        data = [i for i in data if not i.request_task.isend]
        odata = len([i for i in data if not i.request_task.loss_efficacy])
    except:
        odata = 0
    nums['myaudittasks'] = odata
    return nums


@login_required
def conf_list(request):
    data_huidu = git_deploy.objects.filter(platform="现金网", classify="huidu", isops=True, islog=True)
    data_test = git_deploy.objects.filter(platform="现金网", classify="test", isops=True, islog=True)
    data_online = git_deploy.objects.filter(platform="现金网", classify="online", isops=True, islog=True)
    alone = git_deploy.objects.filter(platform="单个项目", classify="online", isops=True, islog=True)
    return render(request, 'gitfabu/conf_list.html', locals())


@login_required
def version_list(request, uuid):
    data = git_deploy.objects.get(pk=uuid)
    if data.old_reversion:
        old_reversion = data.old_reversion.split('\r\n')
    else:
        old_reversion = []
    return render(request, 'gitfabu/version_list.html', locals())


def deploy_domains(request):
    classify = request.GET.get('classify')
    siteid = request.GET.get('siteid')
    platform = request.GET.get('platform')
    business = Business.objects.get(platform=platform, status=0, nic_name=siteid)
    f = business.domain.filter(use=0, classify=classify)
    a = business.domain.filter(use=1, classify=classify)
    b = business.domain.filter(use=2, classify=classify)
    webtext = "\n".join([i.name for i in f if i])
    agtext = "\n".join([i.name for i in a if i])
    ds168text = "\n".join([i.name for i in b if i])
    return JsonResponse({"webtext": webtext, "agtext": agtext, "ds168text": ds168text}, safe=False)


@login_required
def conf_add_alone_project(request):
    """单独项目添加，需要配置服务器，git地址，线上目录"""
    project = "现金网"
    export_dir = "/data/onlyproject/online/export/"
    errors = []
    if request.method == "POST":
        name = request.POST.get("name")
        memo = request.POST.get("memo")
        git_branch = request.POST.get("git_branch")
        git_commit = request.POST.get("git_commit")
        repo = request.POST.get("repo")

        if not "http" in repo:
            errors.append("git地址有错误！缺少http关键字")

        git_export = export_dir + name

        remoteip = request.POST.get("remoteip")
        for i in remoteip.split('\r\n'):
            try:
                Server.objects.get(ssh_host=i)
            except:
                errors.append("CMDB中无此IP：%s" % i)

        remotedir = request.POST.get("remotedir")
        owner = request.POST.get("owner")
        exclude = request.POST.get("exclude")
        rsync_command = request.POST.get("rsync_command")
        last_command = request.POST.get("last_command")

        #if git_coderepo.objects.filter(title=name,classify="online",platform="单个项目"): errors.append("已有相关项目git地址配置,请检查是否有重名项目！")
        #if git_ops_configuration.objects.filter(name=name,classify="online",platform="单个项目"): errors.append("已有相关项目服务器配置,请检查是否有重名项目！")

        if errors:
            return render(request, 'gitfabu/add_alone_project.html', locals())

        # 先存储服务器相关配置
        obj, server_data = git_ops_configuration.objects.get_or_create(name=name, classify="online", platform="单个项目", defaults={'remoteip': remoteip, 'remotedir': remotedir, 'owner': owner, "exclude": exclude, "rsync_command": rsync_command, "last_command": last_command})
        if obj:
            server_data = obj
        else:
            server_data = server_data
        # 再存储git相关配置
        obj, repo_data = git_coderepo.objects.get_or_create(title=name, classify="online", platform="单个项目", defaults={"address": repo, "user": "fabu", "passwd": "DSyunweibu110110", "branch": git_branch, "reversion": git_commit})
        # 先创建git_deploy实例
        deploy_obj, deploy = git_deploy.objects.get_or_create(name=name, platform="单个项目", classify="online", server=server_data, isdev=True, isops=True)
        if obj:
            data = deploy_obj
        else:
            data = deploy
        # 最后创建审核任务，分发审核,因为运维直接参与配置所以不需要审核
        mydata = my_request_task(name=name + "_线上发布", table_name="git_deploy", uuid=data.id, initiator=request.user, memo=memo, status="发布中")
        mydata.save()
        reslut = git_fabu_task.delay(data.id, mydata.id)
        return HttpResponseRedirect('/fabu/mytask/')
    return render(request, 'gitfabu/add_alone_project.html', locals())


@login_required
def conf_add_java_project(request):
    """单独项目添加，需要配置服务器，git地址，线上目录"""
    project = "蛮牛JAVA"
    export_dir = "/data/javaproject/online/export/"
    errors = []
    if request.method == "POST":
        name = request.POST.get("name")
        memo = request.POST.get("memo")
        git_branch = request.POST.get("git_branch")
        git_commit = request.POST.get("git_commit")
        repo = request.POST.get("repo")

        if not "http" in repo:
            errors.append("git地址有错误！缺少http关键字")

        git_export = export_dir + name

        remoteip = request.POST.get("remoteip")
        for i in remoteip.split('\r\n'):
            try:
                Server.objects.get(ssh_host=i)
            except:
                errors.append("CMDB中无此IP：%s" % i)

        remotedir = request.POST.get("remotedir")
        owner = request.POST.get("owner")
        exclude = request.POST.get("exclude")
        rsync_command = request.POST.get("rsync_command")
        last_command = request.POST.get("last_command")

        #if git_coderepo.objects.filter(title=name,classify="online",platform="JAVA项目"): errors.append("已有相关项目git地址配置,请检查是否有重名项目！")
        #if git_ops_configuration.objects.filter(name=name,classify="online",platform="JAVA项目"): errors.append("已有相关项目服务器配置,请检查是否有重名项目！")

        if errors:
            return render(request, 'gitfabu/add_alone_project.html', locals())

        # 先存储服务器相关配置
        obj, server_data = git_ops_configuration.objects.get_or_create(name=name, classify="online", platform="JAVA项目", defaults={'remoteip': remoteip, 'remotedir': remotedir, 'owner': owner, "exclude": exclude, "rsync_command": rsync_command, "last_command": last_command})
        if obj:
            server_data = obj
        else:
            server_data = server_data
        # 再存储git相关配置
        obj, repo_data = git_coderepo.objects.get_or_create(title=name, classify="online", platform="JAVA项目", defaults={"address": repo, "user": "fabu", "passwd": "DSyunweibu110110", "branch": git_branch, "reversion": git_commit})
        # 先创建git_deploy实例
        deploy_obj, deploy = git_deploy.objects.get_or_create(name=name, platform="JAVA项目", classify="online", server=server_data, isdev=True, isops=True)
        if obj:
            data = deploy_obj
        else:
            data = deploy
        # 最后创建审核任务，分发审核,因为运维直接参与配置所以不需要审核
        mydata = my_request_task(name=name + "_线上发布", table_name="git_deploy", uuid=data.id, initiator=request.user, memo=memo, status="发布中")
        mydata.save()
        reslut = git_fabu_task.delay(data.id, mydata.id)
        return HttpResponseRedirect('/fabu/mytask/')
    return render(request, 'gitfabu/add_alone_project.html', locals())


@login_required
def conf_add(request, env):
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
    elif "vue" in env:
        platform = "VUE蛮牛"
        conf_domain = True
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
    deploy = [i.name for i in git_deploy.objects.filter(platform=platform, classify=envir, isops=True, islog=True)]

    busi = []  # 只显示没有发布过的项目
    for i in Business.objects.filter(platform=platform, status=0):
        if i.nic_name not in deploy:
            busi.append(i)

    if request.method == 'POST':
        name = request.POST.get('business')  # 所有发布的项目使用business中的nic_name当作名称
        gg = git_deploy.objects.filter(name=name, platform=platform, classify=envir)  # 除非把已存在的没完成的作废掉,否则不许重发
        if len(gg) > 0:
            errors.append("项目以存在，请联系运维处理")
        business = Business.objects.get(nic_name=name)

        # 配置服务器地址，没有配置会报错，所以使用try
        try:
            if platform == "现金网":
                server = git_ops_configuration.objects.get(name="源站", platform="现金网", classify=envir)
            elif platform == "VUE蛮牛" or platform == "蛮牛":
                server = git_ops_configuration.objects.get(name="源站", platform="蛮牛", classify=envir)
            else:
                server = git_ops_configuration.objects.get(name=name, platform=platform, classify=envir)
        except:
            errors.append("没有配置-%s-%s-%s-服务器地址" % (platform, business.name, envir))

        # 检测域名正确性，测试环境不会检查ag与backend域名,发布Huidu的时候需要填写后台域名，发布线上的时候需要填写前台与ag域名
        # 蛮牛现金网副网不检测域名后台
        # C网
        if platform == "现金网" or platform == "蛮牛" or platform == "VUE蛮牛":
            f_domainname = DomainName.objects.filter(use=0, business=business, classify=envir)
            a_domainname = DomainName.objects.filter(use=1, business=business, classify=envir)
            b_domainname = DomainName.objects.filter(use=2, business=business, classify=envir)
            if f_domainname:
                f_domainname = [i.name for i in f_domainname]
            else:
                errors.append("没有给出前端域名,请联系产品添加域名")

            if envir != "test":
                print platform
                if a_domainname:
                    a_domainname = [i.name for i in a_domainname]
                else:
                    errors.append("没有给出ag域名,请联系产品添加域名")
                if b_domainname:
                    b_domainname = [i.name for i in b_domainname]
                else:
                    errors.append("没有给出后台域名,请联系产品添加域名")

        if errors:
            return render(request, 'gitfabu/conf_add.html', locals())

        # 配置git地址，如果没有找到web/1001.git类似的私有仓库，则创建保存
        online_git = "http://git.dtops.cc/"
        username = "fabu"  # 写死的，以后会是一个bug
        password = "DSyunweibu110110"
        if platform == "现金网":  # 注意：只有现金网和蛮牛的web项目发布时才会创建git地址，其他的单独项目和JAVA项目应该手动添加git的相关信息
            web = online_git + "web/%s.git" % name
            obj, created = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=False, title=name, defaults={'address': web, 'user': username, 'passwd': password},)
            php_pc, php_pc_repo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="php_pc", defaults={'address': online_git + "php/1000_public_php.git", 'user': username, 'passwd': password})
            php_mob, php_mob_repo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="php_mobile", defaults={'address': online_git + "php/1000m_public_php.git", 'user': username, 'passwd': password})
            js_pc, js_pc_repo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="js_pc", defaults={'address': online_git + "web/1000_public_js.git", 'user': username, 'passwd': password})
            js_mob, js_mob_repo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="js_mobile", defaults={'address': online_git + "web/1000m_public_js.git", 'user': username, 'passwd': password})
            configobj, configrepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=False, title=name + "_config", defaults={'address': online_git + "config/" + name + ".git", 'user': username, 'passwd': password})
        elif platform == "蛮牛":
            if envir == "huidu":
                php_repo = online_git + "harrisdt15f/huidu-wcphpsec.git"
            elif envir == "test":
                username = "dtops"
                php_repo = "http://git.ds.com/harrisdt15f1/neiwang_wcphpsec.git"
            else:
                php_repo = online_git + "harrisdt15f/wcphpsec.git"
            web = online_git + "jack/%s.git" % name
            obj, created = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=False, title=name, defaults={'address': web, 'user': username, 'passwd': password},)
            jsobj, jsrepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="mn_js", defaults={'address': online_git + "jack/mn-web-public.git", 'user': username, 'passwd': password})
            phpobj, phprepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="mn_php", defaults={'address': php_repo, 'user': username, 'passwd': password})
            configobj, configrepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="mn_config", defaults={'address': online_git + "harrisdt15f/phpcofig.git", 'user': username, 'passwd': password})
        elif platform == "VUE蛮牛":
            if envir == "huidu":
                php_repo = "http://git.dtops.cc/harrisdt15f/huidu-wcphpsec.git"
                php_config = "http://git.dtops.cc/harrisdt15f/phpcofig.git"
            elif envir == "test":
                username = "dtops"
                password = "DSyunweibu110110"
                online_git = "http://git.ds.com/"
                php_repo = "http://git.ds.com/harrisdt15f1/wcphpsec.git"
                php_config = "http://git.ds.com/harrisdt15f1/phpcofig.git"
            else:
                php_repo = "http://git.dtops.cc/harrisdt15f/wcphpsec.git"
                php_config = "http://git.dtops.cc/harrisdt15f/phpcofig.git"
            pc_addr = online_git + "dt-vue-group/pc/" + name.replace("vue", ".git")
            wap_addr = online_git + "dt-vue-group/m/" + name.replace("vue", ".git")

            vuepc, pcrepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=False, title=name + "_mn_pc", defaults={'address': pc_addr, 'user': username, 'passwd': password},)
            vuewap, waprepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=False, title=name + "_mn_wap", defaults={'address': wap_addr, 'user': username, 'passwd': password})
            phpobj, phprepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="vue_mn_php", defaults={'address': php_repo, 'user': username, 'passwd': password})
            configobj, configrepo = git_coderepo.objects.get_or_create(platform=platform, classify=envir, ispublic=True, title="vue_mn_config", defaults={'address': online_git + "harrisdt15f/phpcofig.git", 'user': username, 'passwd': password})

        ddata, created = git_deploy.objects.get_or_create(name=name, platform=platform, classify=envir, business=business, defaults={'conf_domain': conf_domain, 'server': server, 'usepub': conf_domain, 'isdev': True},)

        # 保存配置域名
        # if platform == "现金网" or platform == "蛮牛":
        #     for i in f_domainname:
        #         obj,created = DomainName.objects.get_or_create(name=i,use='0',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)
        #     if envir != "test":
        #         for i in a_domainname:
        #             obj,created = DomainName.objects.get_or_create(name=i,use='1',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)
        #         for i in b_domainname:
        #             obj,created = DomainName.objects.get_or_create(name=i,use='2',business=business,classify=envir,defaults={'state':'0','supplier':"工程"},)

        # 分配审核任务
        task_name = "%s--%s" % (dname, name)
        memo = "%s,%s环境,%s发布" % (platform, envname, name)
        mydata = my_request_task(name=task_name, types="fabu", table_name="git_deploy", uuid=ddata.id, initiator=request.user, memo=memo, status="审核中")
        mydata.save()
        if envir == 'test':  # 测试环境直接发布，其他环境需要分发审核任务
            mydata.status = "发布中"
            mydata.save()
            reslut = git_fabu_task.delay(ddata.id, mydata.id)
        else:
            if platform == "VUE蛮牛":
                auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=envir, name="发布")
            else:
                auditor = git_deploy_audit.objects.get(platform=platform, classify=envir, name="发布")
            send_message_task.delay(mydata.id, auditor.id)
        return HttpResponseRedirect('/allow/welcome/')
    return render(request, 'gitfabu/conf_add.html', locals())


@login_required
def my_request_task_list(request):

    if request.user.username == "wuhf":
        data = my_request_task.objects.filter(isend=False, loss_efficacy=False).order_by('-create_date')
    else:
        data = my_request_task.objects.filter(initiator=request.user, loss_efficacy=False).order_by('-create_date')[0:100]
    # data = my_request_task.objects.filter(initiator=request.user,loss_efficacy=True).order_by('-create_date')[0:100]
    return render(request, 'gitfabu/my_request_task.html', locals())




@login_required
def my_request_task_filter(request):
    task_filter=request.GET.get('task_filter')
    page=request.GET.get('page')
    limit=request.GET.get('limit')
    if page==1:
        start_line=0
        end_line=limit
    else:
        start_line=int(page)*int(limit)-int(limit)
        end_line=int(page)*int(limit)

    if not task_filter:
        if request.user.is_superuser:
            data = my_request_task.objects.filter(loss_efficacy=False).order_by('-create_date')[start_line:end_line]
        else:
            data = my_request_task.objects.filter(initiator=request.user, loss_efficacy=False).order_by('-create_date')[start_line:end_line]
        task_data={"code":0,"msg":"","count":150,"data":[]}
        
        for task in data:
            others_task=task.reqt.all()
            others_task_dict={}
            for gid in list(set(i.audit_group_id for i in others_task)):
                try:
                    GroupName=department_Mode.objects.get(pk=gid).name
                except:
                    GroupName="ungroup"
                others_task_dict[GroupName]=[]
            for j in others_task:
                try:
                    GroupName=department_Mode.objects.get(pk=j.audit_group_id).name
                except:
                    GroupName="ungroup"
                if j.isaudit:
                    if j.ispass:
                        others_task_dict[GroupName].append({j.auditor.username:"yes"})
                    else:
                        others_task_dict[GroupName].append({j.auditor.username:"no"})
                else:
                    others_task_dict[GroupName].append({j.auditor.username:"wait"})
            task_data["data"].append({"id":task.id,"isend":task.isend,"ttype":task.types,"datetime":task.create_date.strftime('%Y-%m-%d %H:%M:%S'),"taskname":task.name,"status":task.status,"audit":others_task_dict})
        return JsonResponse(task_data)
    else:
        platform=request.GET.get('platform')
        classify=request.GET.get('classify')
        wtype=request.GET.get('wtype')
        status=request.GET.get('status')
        loss_efficacy=request.GET.get('loss_efficacy')
        counts=request.GET.get('counts')
        if counts=='all':counts='2000'
        counts=int(counts)
        if status=="preparing":
            isend=False
        else:
            isend=True
        if loss_efficacy=="yes":
            loss=True
        else:
            loss=False
        if classify=="online":
            env="线上"
        elif classify=="huidu":
            env="灰度"
        else:
            env="测试"
        if wtype=="更新":
            filter_string=platform+"-"+classify
            types='gengxin'
        else:
            filter_string=platform+"_"+env
            types='fabu'
        if request.user.is_superuser:
            data = my_request_task.objects.filter(isend=isend, loss_efficacy=loss,name__contains=filter_string).order_by('-create_date')[start_line:end_line]
        else:
            data = my_request_task.objects.filter(initiator=request.user,isend=isend, loss_efficacy=loss,name__contains=filter_string).order_by('-create_date')[start_line:end_line]
        task_data={"code":0,"msg":"","count":counts,"data":[]}
        for task in data:
            others_task=task.reqt.all()
            others_task_dict={}
            for gid in list(set(i.audit_group_id for i in others_task)):
                try:
                    GroupName=department_Mode.objects.get(pk=gid).name
                except:
                    GroupName="ungroup"
                others_task_dict[GroupName]=[]
            for j in others_task:
                try:
                    GroupName=department_Mode.objects.get(pk=j.audit_group_id).name
                except:
                    GroupName="ungroup"
                if j.isaudit:
                    if j.ispass:
                        others_task_dict[GroupName].append({j.auditor.username:"yes"})
                    else:
                        others_task_dict[GroupName].append({j.auditor.username:"no"})
                else:
                    others_task_dict[GroupName].append({j.auditor.username:"wait"})
            task_data["data"].append({"id":task.id,"isend":task.isend,"ttype":task.types,"datetime":task.create_date.strftime('%Y-%m-%d %H:%M:%S'),"taskname":task.name,"status":task.status,"audit":others_task_dict})
        return JsonResponse(task_data)



@login_required
def others_request_task_list(request):
    if request.user.username == "wuhf":
        # data = []
        # ll = []
        # sdata = my_request_task.objects.filter(isend=False,loss_efficacy=False)
        # for i in sdata:
        #     for j in i.reqt.all():
        #         data.append(j)
        data = git_task_audit.objects.filter(isaudit=False, loss_efficacy=False)[0:100]
    else:
        data = git_task_audit.objects.filter(auditor=request.user).order_by('-create_date')[0:100]
    # data = git_task_audit.objects.filter(auditor=request.user,loss_efficacy=False).order_by('-create_date')[0:100]
    return render(request, 'gitfabu/others_request_task.html', locals())

@login_required
def others_request_task_filter(request):
    task_filter=request.GET.get('task_filter')
    page=request.GET.get('page')
    limit=request.GET.get('limit')
    if not page:page=1
    if not limit:limit=200
    if page==1:
        start_line=0
        end_line=limit
    else:
        start_line=int(page)*int(limit)-int(limit)
        end_line=int(page)*int(limit)
    if not task_filter:
        if request.user.is_superuser:
            data = git_task_audit.objects.filter(isaudit=False)[start_line:end_line]
        else:
            data = git_task_audit.objects.filter(auditor=request.user).order_by('-create_date')[start_line:end_line]
        task_data={"code":0,"msg":"","count":150,"data":[]}
        for task in data:
            showbtn=False
            if task.request_task.isend:
                isaudit="此任务已结束"
            else:
                if task.isaudit:
                    if task.ispass:
                        isaudit="已通过"
                    else:
                        isaudit="未通过"
                else:
                    isaudit="未审核"
                    showbtn=True
            if task.request_task.loss_efficacy:
                showbtn=False
            task_data["data"].append({"id":task.id,"rid":task.request_task.id,"showbtn":showbtn,"auditor":task.auditor.username,"tasktypes":task.request_task.types,"audit_status":isaudit,"datetime":task.create_date.strftime('%Y-%m-%d %H:%M:%S'),"isend":task.request_task.isend,"isaudit":task.isaudit,"ispass":task.ispass,"postil":task.postil,"loss_efficacy":task.loss_efficacy,"taskname":task.request_task.name,"status":task.request_task.status,"memo":task.request_task.memo,"initiator":task.request_task.initiator.username})
    else:
        platform=request.GET.get('platform')
        classify=request.GET.get('classify')
        wtype=request.GET.get('wtype')
        status=request.GET.get('status')
        loss_efficacy=request.GET.get('loss_efficacy')
        if status=="preparing":
            isend=False
        else:
            isend=True
        if classify=="online":
            env="线上"
        elif classify=="huidu":
            env="灰度"
        else:
            env="测试"
        if wtype=="更新":
            filter_string=platform+"-"+classify
            types='gengxin'
        else:
            filter_string=platform+"_"+env
            types='fabu'
        if request.user.is_superuser:
            data = git_task_audit.objects.filter(loss_efficacy=False,isaudit=isend)[start_line:end_line]
        else:
            data = git_task_audit.objects.filter(loss_efficacy=False,auditor=request.user).order_by('-create_date')[start_line:end_line]
        data = [i for i in data if i.request_task.isend == isend]
        task_data={"code":0,"msg":"","count":150,"data":[]}
        for task in [obj for obj in data if filter_string in obj.request_task.name]:
            showbtn=False
            if task.request_task.isend:
                isaudit="此任务已结束"
            else:
                if task.isaudit:
                    if task.ispass:
                        isaudit="已通过"
                    else:
                        isaudit="未通过"
                else:
                    isaudit="未审核"
                    showbtn=True
            if task.request_task.loss_efficacy:
                showbtn=False
            task_data["data"].append({"id":task.id,"rid":task.request_task.id,"showbtn":showbtn,"auditor":task.auditor.username,"tasktypes":task.request_task.types,"audit_status":isaudit,"datetime":task.create_date.strftime('%Y-%m-%d %H:%M:%S'),"isend":task.request_task.isend,"isaudit":task.isaudit,"ispass":task.ispass,"postil":task.postil,"loss_efficacy":task.loss_efficacy,"taskname":task.request_task.name,"status":task.request_task.status,"memo":task.request_task.memo,"initiator":task.request_task.initiator.username})

    return JsonResponse(task_data)

@login_required
def cancel_my_task(request, uuid):
    data = my_request_task.objects.get(id=uuid)
    data.loss_efficacy = True
    data.status = "已停止"
    data.reqt.all().update(loss_efficacy=True)  # 停止相关的审核任务
    data.save()  # 停止此次申请任务，还应当将锁住的项目解锁
    if "batch" not in data.types:
        df = eval(data.table_name).objects.get(pk=data.uuid)
        if data.table_name == "git_code_update":
            if df.code_conf:  # 单个更新任务，删除任务，解锁项目
                df.code_conf.islock = False
                df.code_conf.save()
            else:  # 集体更新任务处理
                if "现金网" in df.name:
                    platform = "现金网"
                if "蛮牛" in df.name:
                    platform = "蛮牛"
                if "VUE" in df.name:
                    platform = "VUE蛮牛"
                if "huidu" in df.name:
                    classify = "huidu"
                if "online" in df.name:
                    classify = "online"
                if "test" in df.name:
                    classify = "test"
                git_deploy.objects.filter(platform=platform, classify=classify, islog=True, usepub=True).update(islock=False)
        df.delete()  # 只删除更新任务,发布任务和sql申请审核任务不删除
    return JsonResponse({'res': "已经终止申请"}, safe=False)


@login_required
def my_task_details(request, uuid):
    data = my_request_task.objects.get(id=uuid)
    others_data = data.reqt.all().order_by('audit_time')  # 分发的审核任务
    groups = list(set([i.audit_group_id for i in others_data if i]))  # 拿到审核组的ID
    groups = [department_Mode.objects.get(id=i) for i in groups]  # 拿到审核组的对象集合
    res = {}
    for i in groups:  # 组遍历，组织一个dist：{"GroupName":{"member":[组员审核信息],"date":"","time":"","status":""}}
        L = []
        status = "该组未审核"
        others_data = data.reqt.filter(audit_group_id=str(i.id)).order_by('audit_time')

        pass_data = data.reqt.filter(audit_group_id=str(i.id), isaudit=True, ispass=True)
        if pass_data:
            status = "该组已通过"
        nopass_data = data.reqt.filter(audit_group_id=str(i.id), isaudit=True, ispass=False)
        if nopass_data:
            status = "该组未通过"

        for j in others_data:
            L.append({"name": j.auditor.first_name, "isaudit": j.isaudit, "ispass": j.ispass, "time": j.audit_time.strftime('%Y-%m-%d %H:%M:%S'), "postil": j.postil})

        res[i.name] = {"member": L, "date": j.audit_time.strftime('%Y-%m-%d'), "time": j.audit_time.strftime('%H:%M:%S'), "status": status}

    if data.loss_efficacy:
        return render(request, 'gitfabu/my_task_details.html', locals())
    if "batch" in data.types:
        classify = "batch"
        types = data.types.split("-")
        platform = types[0]
        env = types[1]
        batch = types[2]
        method = types[3]
        name = data.name
        memos = eval(data.memo)
        try:
            dflog = git_deploy_logs.objects.get(update=data.uuid)
        except:
            dflog = None
    else:
        if data.table_name == "git_deploy":
            classify = "fabu"
            try:
                df = eval(data.table_name).objects.get(pk=data.uuid)
            except:
                return render(request, 'gitfabu/my_task_details.html', locals())
            dflog = df.deploy_logs.filter(name="发布")
            auditors = git_deploy_audit.objects.filter(platform=df.platform, classify=df.classify, name="发布")
            gitprivate = git_coderepo.objects.filter(platform=df.platform, classify=df.classify, ispublic=False, title=df.name)
            if df.platform == "现金网" or df.platform == "蛮牛" or df.platform == "VUE蛮牛":
                fabu_details = True
                domains = df.business.domain.filter(classify=df.classify, use=0).order_by('name')
                ag_domains = df.business.domain.filter(classify=df.classify, use=1).order_by('name')
                backend_domains = df.business.domain.filter(classify=df.classify, use=2).order_by('name')
                gitpublic = git_coderepo.objects.filter(platform=df.platform, classify=df.classify, ispublic=True)
                if df.platform == "VUE蛮牛":
                    auditors = git_deploy_audit.objects.filter(platform="蛮牛", classify=df.classify, name="发布")
                    gitprivate = git_coderepo.objects.filter(platform=df.platform, classify=df.classify, ispublic=False, title__contains=df.name)
                    servers = git_ops_configuration.objects.filter(platform="蛮牛", classify=df.classify, name="源站")
                else:
                    servers = git_ops_configuration.objects.filter(platform=df.platform, classify=df.classify, name="源站")
            else:
                fabu_details = False
                domains = None
                servers = git_ops_configuration.objects.filter(platform=df.platform, classify=df.classify, name=df.name)
        elif data.table_name == "git_code_update":
            classify = "gengxin"
            df = eval(data.table_name).objects.get(pk=data.uuid)
            deploy_data = df.code_conf
            if deploy_data:  # 如果有项目外键
                dflog = deploy_data.deploy_logs.filter(name="更新", update=df.id)
                if deploy_data.platform == "VUE蛮牛":
                    auditors = git_deploy_audit.objects.filter(platform="蛮牛", classify=deploy_data.classify, name="更新", isurgent=df.isurgent)
                else:
                    auditors = git_deploy_audit.objects.filter(platform=deploy_data.platform, classify=deploy_data.classify, name="更新", isurgent=df.isurgent)
                if df.method == "php_pc" or df.method == "php_mobile" or df.method == "js_pc" or df.method == "js_mobile":
                    name = "%s-电脑端更新" % df.method
                    repo = git_coderepo.objects.get(platform="现金网", classify=deploy_data.classify, title=df.method, ispublic=True).address
                elif df.method == "php" or df.method == "config" or df.method == "js":
                    name = "蛮牛%s-公共代码更新" % df.method
                    repo = git_coderepo.objects.get(platform="蛮牛", classify=deploy_data.classify, title="mn_" + df.method, ispublic=True).address
                elif df.method == "vue_php" or df.method == "vue_config":
                    name = "VUE蛮牛%s-代码更新" % df.method
                    repo = git_coderepo.objects.get(platform="VUE蛮牛", classify=deploy_data.classify, title=df.method.replace("vue", "vue_mn"), ispublic=True).address
                elif df.method == "vue_pc" or df.method == "vue_wap":
                    name = "VUE蛮牛%s-代码更新" % df.method
                    print deploy_data.name + df.method.replace("vue", "_mn")
                    repo = git_coderepo.objects.get(platform="VUE蛮牛", classify=deploy_data.classify, title=deploy_data.name + df.method.replace("vue", "_mn"), ispublic=False).address
                else:
                    name = "%s-更新" % deploy_data.name
                    repo = git_coderepo.objects.get(platform=deploy_data.platform, classify=deploy_data.classify, ispublic=False, title=deploy_data.name).address
                version = df.version
                branch = df.branch
                version_details = df.details
            else:  # 没有项目外键，判断属于公共代码全部更新
                dflog = git_deploy_logs.objects.filter(name="更新", update=df.id)
                if "huidu" in df.name:
                    env = "huidu"
                if "online" in df.name:
                    env = "online"
                if "test" in df.name:
                    env = "test"
                if "现金网" in df.name:
                    platform = "现金网"
                if "蛮牛" in df.name:
                    platform = "蛮牛"
                if "VUE" in df.name:
                    platform = "VUE蛮牛"
                if env == "test":
                    auditors = None
                else:
                    if platform == "VUE蛮牛":
                        auditors = git_deploy_audit.objects.filter(platform="蛮牛", classify=env, name="更新", isurgent=df.isurgent)
                    else:
                        auditors = git_deploy_audit.objects.filter(platform=platform, classify=env, name="更新", isurgent=df.isurgent)
                if df.method == "php_pc" or df.method == "php_mobile" or df.method == "js_pc" or df.method == "js_mobile":
                    repo = git_coderepo.objects.get(platform=platform, classify=env, title=df.method, ispublic=True).address
                    name = "%s-电脑端更新" % df.method
                elif df.method == "php" or df.method == "config" or df.method == "js":
                    repo = git_coderepo.objects.get(platform=platform, classify=env, title="mn_" + df.method, ispublic=True).address
                    name = "蛮牛%s-公共代码更新" % df.method
                elif df.method == "vue_php" or df.method == "vue_config":
                    name = "VUE蛮牛%s-代码更新" % df.method
                    repo = git_coderepo.objects.get(platform=platform, classify=env, title=df.method.replace("vue", "vue_mn"), ispublic=True).address
                version = df.version
                branch = df.branch
                version_details = df.details
        elif data.table_name == "sql_apply":
            classify = "sql"
            df = eval(data.table_name).objects.get(pk=data.uuid)
            sql_conf = df.name
            dflog = df.log

    return render(request, 'gitfabu/my_task_details.html', locals())


def confirm_mytask(request, uuid):
    """实现get方式复核，将git_deploy的isops为真，mytask的ispass为真"""
    mytask = git_task_audit.objects.get(pk=uuid)
    task = mytask.request_task
    df = eval(task.table_name).objects.get(pk=task.uuid)
    f_domains = df.business.domain.filter(classify=df.classify, use=0).order_by('name')  # use=0前端域名，1为ag域名，2为后台域名
    a_domains = df.business.domain.filter(classify=df.classify, use=1).order_by('name')
    b_domains = df.business.domain.filter(classify=df.classify, use=2).order_by('name')
    if request.method == "POST":
        # 重置网站状态
        ok = request.POST.get('isok')
        print ok
        if ok == "yes":
            WebSite = eval(task.table_name).objects.filter(pk=task.uuid)
            WebSite.update(isops=True)
            # 修改任务状态
            task.isend = True
            task.status = "已完成"
            task.save()
            # 修改审核任务状态
            mytask.isaudit = True
            mytask.ispass = True
            mytask.save()
            # 重置其他组任务状态
            user = request.user
            groups = task.reqt.filter(auditor=user)
            postil = "复核完成"
            # 目前只有工程一个组，如果是多个组，下面还要写判断
            for i in groups:
                check_group_audit(task.id, user.username, True, i.audit_group_id, postil)
            return JsonResponse({'res': "OK"}, safe=False)
        else:
            return JsonResponse({'res': "OK"}, safe=False)
    return render(request, 'gitfabu/confirm_mytask.html', locals())


@login_required
def audit_my_task(request, uuid):
    """审核任务，分发布与更新的审核后续处理"""
    data = git_task_audit.objects.get(pk=uuid)
    if request.method == 'POST':
        if data.isaudit:
            return JsonResponse({'res': "OK"}, safe=False)  # 防止重复审核
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

        groups_isaudit = get_the_group_audit_result(data.request_task.id)

        if "batch" in data.request_task.types:  # 批量任务审核
            if data.request_task.reqt.filter(isaudit=True, ispass=False):  # 已审核人里有人否决了任务
                data.request_task.status = "未通过审核"
                data.request_task.isend = True
                data.request_task.save()
                return JsonResponse({'res': "OK"}, safe=False)
            if False not in groups_isaudit:
                data.request_task.status = "通过审核，更新中"
                data.request_task.save()
                reslut = git_batch_update_task.delay(data.request_task.id)
        else:  # 其他任务审核,这一个分支太复杂了,要大修改
            df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
            if data.request_task.reqt.filter(isaudit=True, ispass=False):  # 已审核人里有人否决了任务
                data.request_task.status = "未通过审核"
                data.request_task.isend = True
                data.request_task.save()
                df.isaudit = True  # 更新任务已审核
                df.islog = True  # 更新任务已完成
                if data.request_task.table_name == "git_code_update":
                    if df.code_conf:
                        df.code_conf.islock = False
                        df.code_conf.save()
                    else:
                        if "现金网" in df.name:
                            platform = "现金网"
                        if "蛮牛" in df.name:
                            platform = "蛮牛"
                        if "VUE" in df.name:
                            platform = "VUE蛮牛"
                        if "huidu" in df.name:
                            classify = "huidu"
                        if "online" in df.name:
                            classify = "online"
                        git_deploy.objects.filter(platform=platform, classify=classify, islock=True).update(islock=False)

                df.save()
                return JsonResponse({'res': "OK"}, safe=False)
            if False not in groups_isaudit:  # 所有的组都有人已审核通过
                df.isaudit = True
                df.save()

                if data.request_task.table_name == "git_deploy":  # 发布任务
                    data.request_task.status = "通过审核，发布中"
                    data.request_task.save()
                    reslut = git_fabu_task.delay(df.id, data.request_task.id)
                elif data.request_task.table_name == "git_code_update":  # 更新任务
                    data.request_task.status = "通过审核，更新中"
                    data.request_task.save()
                    if df.code_conf:
                        reslut = git_update_task.delay(data.request_task.uuid, data.request_task.id)
                    else:
                        if "现金网" in df.name:
                            platform = "现金网"
                        if "蛮牛" in df.name:
                            platform = "蛮牛"
                        if "VUE" in df.name:
                            platform = "VUE蛮牛"
                        reslut = git_update_public_task.delay(data.request_task.uuid, data.request_task.id, platform=platform)
                else:  # 数据库审核任务
                    data.request_task.status = "通过审核"
                    data.request_task.save()
        return JsonResponse({'res': "OK"}, safe=False)
    return render(request, 'gitfabu/audit_my_task.html', locals())


@login_required
def one_key_task(request, uuid):
    data = git_task_audit.objects.get(pk=uuid)
    df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
    print "项目id：%s任务id：%s" % (df.id, data.request_task.id)
    if request.method == 'POST':
        if data.isaudit:
            return JsonResponse({'res': "OK"}, safe=False)  # 防止重复审核
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
        onekey_access(data.request_task.id, request.user.username, ok)
        if ok:
            df.isaudit = True
            df.save()
            print "项目id：%s任务id：%s" % (df.id, data.request_task.id)
            if data.request_task.table_name == "git_deploy":
                reslut = git_fabu_task.delay(df.id, data.request_task.id)
            else:
                if df.code_conf:
                    reslut = git_update_task.delay(data.request_task.uuid, data.request_task.id)
                else:
                    if "现金网" in df.name:
                        platform = "现金网"
                    if "蛮牛" in df.name:
                        platform = "蛮牛"
                    if "VUE" in df.name:
                        platform = "VUE蛮牛"
                    reslut = git_update_public_task.delay(data.request_task.uuid, data.request_task.id, platform=platform)
        else:
            df.isaudit = True
            df.islog = True
            if data.request_task.table_name == "git_code_update":
                if df.code_conf:
                    df.code_conf.islock = False
                    df.code_conf.save()
                else:
                    if "现金网" in df.name:
                        platform = "现金网"
                    if "蛮牛" in df.name:
                        platform = "蛮牛"
                    if "VUE" in df.name:
                        platform = "VUE蛮牛"
                    if "huidu" in df.name:
                        classify = "huidu"
                    if "online" in df.name:
                        classify = "online"
                    git_deploy.objects.filter(platform=platform, classify=classify, islock=True).update(islock=False)
            df.save()
        return JsonResponse({'res': "OK"}, safe=False)
    return render(request, 'gitfabu/one_key_task.html', locals())


@login_required
def web_update_code(request, uuid):
    """一个更新任务添加，现获取所有的分支信息，线上环境只有master分支展示"""
    data = git_deploy.objects.get(pk=uuid)

    WaitTask = data.deploy_update.filter(islog=False)
    if not WaitTask:
        WaitTask = git_code_update.objects.filter(name__contains=data.platform, islog=False)

    if data.old_reversion:
        old_reversion = data.old_reversion.split('\r\n')[0:5]
    else:
        old_reversion = []

    if request.method == 'GET':
        if data.platform == "现金网" or data.platform == "蛮牛" or data.platform == "VUE蛮牛":
            all_branch = ['master']
            web_commits = []
        else:
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what='web')
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what='web')

    if request.method == 'POST':
        # 先判断这个站是否被锁住了，没有锁就继续
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')
        # 获取当前版本号,组成新版本信息
        old_data = git_code_update.objects.get(code_conf=data, islog=True, isuse=True)
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
        elif method == "php_pc" or method == "php" or method == "vue_php":
            php_pc_release = release[0:7]
            php_pc_branches = branch
        elif method == "php_mobile":
            php_moblie_release = release[0:7]
            php_mobile_branches = branch
        elif method == "js_pc" or method == "js" or method == "vue_pc":
            js_pc_release = release[0:7]
            js_pc_branches = branch
        elif method == "js_mobile" or method == "vue_wap":
            js_mobile_release = release[0:7]
            js_mobile_branches = branch
        else:
            config_branches = branch
            config_release = release[0:7]
        # 判断是否紧急
        isurgent = False
        tail_name = "正常更新"
        if data.platform == "现金网" or data.platform == "蛮牛" or data.platform == "VUE蛮牛":
            if data.classify == 'huidu' or data.classify == 'online':
                if data.platform == "VUE蛮牛":
                    normal_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=data.classify, isurgent=False, name="更新")  # 正常审核人
                    php_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=data.classify, isurgent=False, name="php更新")  # PHP代码正常审核人
                    urgent_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=data.classify, isurgent=True, name="更新")  # 紧急审核人
                else:
                    normal_auditor = git_deploy_audit.objects.get(platform=data.platform, classify=data.classify, isurgent=False, name="更新")  # 正常审核人
                    php_auditor = git_deploy_audit.objects.get(platform=data.platform, classify=data.classify, isurgent=False, name="php更新")  # PHP代码正常审核人
                    urgent_auditor = git_deploy_audit.objects.get(platform=data.platform, classify=data.classify, isurgent=True, name="更新")  # 紧急审核人

                php_list = ["php_pc", "php_mobile", "php", "config", "vue_php", "vue_config"]
                if method in php_list:
                    auditor = php_auditor  # php审核
                else:
                    auditor = normal_auditor  # 前端审核

            if data.classify == 'online':
                c = int(normal_auditor.start_time.replace(":", ""))
                d = int(normal_auditor.end_time.replace(":", ""))
                now = time.strftime('%H:%M', time.localtime(time.time()))
                wday = time.localtime(time.time()).tm_wday  # 0-6代表周一到周日7天,周三为2
                e = int(now.replace(":", ""))
                if wday == 2:
                    c = 500
                    d = 1700
                if c <= e and d >= e:
                    print "正常更新"
                else:
                    print "紧急更新"
                    auditor = urgent_auditor
                    isurgent = True
                    tail_name = "紧急更新"
            name = data.platform + "-" + data.classify + "-" + data.name + "-" + method + "-" + tail_name
            print name
        else:
            name = data.platform + "-" + data.classify + "-" + data.name + "-更新"
            normal_auditor = git_deploy_audit.objects.get(platform=data.platform, classify=data.classify, isurgent=False, name="更新")
            auditor = normal_auditor
            isurgent = False
        # 保存更新版本信息
        updata = git_code_update(name=name, code_conf=data, method=method, version=release[0:7], branch=branch, web_release=web_release, php_pc_release=php_pc_release,
                                 php_moblie_release=php_moblie_release, js_pc_release=js_pc_release, js_mobile_release=js_mobile_release, config_release=config_release,
                                 web_branches=web_branches, php_pc_branches=php_pc_branches, php_mobile_branches=php_mobile_branches, js_pc_branches=js_pc_branches,
                                 js_mobile_branches=js_mobile_branches, config_branches=config_branches, memo=memo, details=release, isurgent=isurgent, last_version=data.now_reversion)
        updata.save()
        # 给此项目上锁
        data.islock = True
        data.save()
        # 创建更新申请
        mydata = my_request_task(name=name, types='gx', table_name="git_code_update", uuid=updata.id, memo=memo, initiator=request.user, status="审核中")
        mydata.save()
        # 创建审核，测试环境不需要审核
        # pdb.set_trace()
        if data.platform == "单个项目":
            # 单个项目的审核是靠ischeck关键字控制,现金网什么是判断是否为test环境,最好都修改为ischeck来控制
            if auditor.ischeck:
                send_message_task.delay(mydata.id, auditor.id)
            else:
                mydata.status = "通过审核，更新中"
                mydata.save()
                updata.isaudit = True
                updata.save()
                reslut = git_update_task.delay(updata.id, mydata.id)
        else:
            if data.name == "new1029a":  # 现金网1029特例
                mydata.status = "通过审核，更新中"
                mydata.save()
                updata.isaudit = True
                updata.save()
                reslut = git_update_task.delay(updata.id, mydata.id)
            else:
                if data.classify == 'huidu' or data.classify == 'online':
                    send_message_task.delay(mydata.id, auditor.id)
                else:
                    mydata.status = "通过审核，更新中"
                    mydata.save()
                    updata.isaudit = True
                    updata.save()
                    reslut = git_update_task.delay(updata.id, mydata.id)
        return JsonResponse({'res': "OK"}, safe=False)
    return render(request, 'gitfabu/web_update_code.html', locals())


def public_update_code(request, env):
    """公共代码更新"""
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"
    print env
    if "money" in env:
        base_export_dir = "/data/moneyweb/" + classify + "/export/php_pc"
        platform = "现金网"
    elif "manniu" in env:
        base_export_dir = "/data/manniuweb/" + classify + "/export/mn_php"
        platform = "蛮牛"
    elif "vue" in env:
        base_export_dir = "/data/manniuvue/" + classify + "/export/mn_php"
        platform = "VUE蛮牛"
    gitrepo = Repo(base_export_dir)
    all_branch = gitrepo.git_all_branch()
    commit = gitrepo.show_commit()
    WaitTask = git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True, islock=True)  # 如果某个站有锁，则无法申请全站更新

    if request.method == 'POST':
        memo = request.POST.get('memo')
        method = request.POST.get('method')
        release = request.POST.get('release')
        branch = request.POST.get('branch')

        # 判断是否紧急,huidu没有紧急
        isurgent = False
        tail_name = "正常更新"
        if classify == 'huidu' or classify == 'online':
            if platform == "VUE蛮牛":
                normal_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=classify, isurgent=False, name="更新")  # 正常审核人
                php_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=classify, isurgent=False, name="php更新")  # PHP代码正常审核人
                urgent_auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=classify, isurgent=True, name="更新")  # 紧急审核人
            else:
                normal_auditor = git_deploy_audit.objects.get(platform=platform, classify=classify, isurgent=False, name="更新")  # 正常审核人
                php_auditor = git_deploy_audit.objects.get(platform=platform, classify=classify, isurgent=False, name="php更新")  # PHP代码正常审核人
                urgent_auditor = git_deploy_audit.objects.get(platform=platform, classify=classify, isurgent=True, name="更新")  # 紧急审核人

            php_list = ["php_pc", "php_mobile", "php", "config", "vue_php", "vue_config"]
            if method in php_list:
                auditor = php_auditor  # php审核
            else:
                auditor = normal_auditor  # 前端审核

        if classify == 'online':
            c = int(normal_auditor.start_time.replace(":", ""))
            d = int(normal_auditor.end_time.replace(":", ""))
            now = time.strftime('%H:%M', time.localtime(time.time()))
            wday = time.localtime(time.time()).tm_wday  # 0-6代表周一到周日7天,周三为2
            e = int(now.replace(":", ""))
            if wday == 2:
                c = 500
                d = 1700
            if c <= e and d >= e:
                print "正常更新"
            else:
                print "紧急更新"
                auditor = urgent_auditor
                isurgent = True
                tail_name = "紧急更新"
        name = platform + "-" + classify + "-" + "-公共代码-" + "-" + method + "-" + tail_name
        print name
        # 保存更新任务
        updata = git_code_update(name=name, method=method, version=release[0:7], branch=branch, memo=memo, details=release, isurgent=isurgent)
        updata.save()
        # 创建更新申请
        mydata = my_request_task(name=name, types='publicgx', table_name="git_code_update", uuid=updata.id, memo=memo, initiator=request.user, status="审核中")
        mydata.save()
        git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True, usepub=True).update(islock=True)  # 迁移的时候别忘记把所有的项目usepub项更新为真
        # 创建审核
        if classify == "test":
            mydata.status = "通过审核，更新中"
            mydata.save()
            updata.isaudit = True
            updata.save()
            reslut = git_update_public_task.delay(updata.id, mydata.id, platform=platform)
        else:
            send_message_task.delay(mydata.id, auditor.id)
        return JsonResponse({'res': "OK"}, safe=False)
    return render(request, 'gitfabu/public_update_code.html', locals())


def ops_confguration(request):
    """配置页面，包含审核人，线上服务器，公用public地址"""
    repo_data = git_coderepo.objects.filter(platform="现金网", ispublic=True)
    audit_data = git_deploy_audit.objects.filter(platform="现金网")
    ops_data = git_ops_configuration.objects.filter(platform="现金网")
    return render(request, 'gitfabu/ops_confguration.html', locals())


def batch_change(request, uuid):
    """切换分支并获取最新的版本号10条"""
    env = request.GET.get('env')
    method = request.GET.get('method')
    branch = request.GET.get('branch')
    if env == "moneyweb":
        print "现金网查询版本号"
        if not method:
            res = {'res': "OK", 'branches': [], "commit": []}
            return JsonResponse(res, safe=False)
        if branch:
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what=method, branch=branch)
            res = {'res': "OK", "commit": web_commits}
        else:
            all_branch = git_moneyweb_deploy(uuid).deploy_all_branch(what=method)
            web_commits = git_moneyweb_deploy(uuid).branch_checkout(what=method)
            res = {'res': "OK", 'branches': all_branch, "commit": web_commits}
    else:
        print "蛮牛网查询版本号"
        if not method:
            res = {'res': "OK", 'branches': [], "commit": []}
            return JsonResponse(res, safe=False)
        if branch:
            web_commits = manniu_web_deploy(uuid).branch_checkout(what=method, branch=branch)
            res = {'res': "OK", "commit": web_commits}
        else:
            data = manniu_web_deploy(uuid)
            all_branch = data.deploy_all_branch(what=method)
            web_commits = manniu_web_deploy(uuid).branch_checkout(what=method)
            res = {'res': "OK", 'branches': all_branch, "commit": web_commits}
    return JsonResponse(res, safe=False)


def public_branch_change(request):
    name = request.GET.get('name')
    env = request.GET.get('env')
    branch = request.GET.get('branch')
    print env

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
    else:
        base_dir = "/data/manniuvue/" + classify + "/export/"
        platform = "VUE蛮牛"

    if name == 'php_pc' or name == 'php_mobile' or name == 'js_pc' or name == 'js_mobile':
        path = base_dir + name
    elif name == 'php' or name == 'js' or name == 'config':
        path = base_dir + "mn_" + name
    elif name == 'vue_php':
        path = base_dir + "mn_php"
    elif name == 'vue_config':
        path = base_dir + "mn_config"
    gitrepo = Repo(path)
    if branch:
        gitrepo.git_checkout(branch)
        gitrepo.git_pull()
        commit = gitrepo.show_commit()
        res = {'res': "OK", "commit": commit}
    else:
        gitrepo.git_checkout('master')
        gitrepo.git_pull()
        all_branch = gitrepo.git_all_branch()
        commit = gitrepo.show_commit()
        res = {'res': "OK", 'branches': all_branch, "commit": commit}
    return JsonResponse(res, safe=False)


@login_required
def manniu_list(request):
    data = git_deploy.objects.filter(platform="JAVA项目", classify="online", isops=True, islog=True)  # 蛮牛java组件项目
    data_huidu = git_deploy.objects.filter(platform="蛮牛", classify="huidu", isops=True, islog=True)
    data_online = git_deploy.objects.filter(platform="蛮牛", classify="online", isops=True, islog=True)
    data_test = git_deploy.objects.filter(platform="蛮牛", classify="test", isops=True, islog=True)
    return render(request, 'gitfabu/manniu_list.html', locals())


@login_required
def audit_list(request):
    data = git_deploy_audit.objects.all().order_by('platform', 'classify')
    return render(request, 'gitfabu/audit_list.html', locals())


def audit_manage(request, uuid):
    data = git_deploy_audit.objects.get(pk=uuid)
    uf = git_deploy_audit_from(instance=data)
    all_group = department_Mode.objects.all()
    select_group = data.group.all()
    unselect_group = [i for i in all_group if i not in select_group]
    if request.method == 'POST':
        print request.POST.get('name')
        uf = git_deploy_audit_from(request.POST, instance=data)
        if uf.is_valid():
            member = uf.save(commit=False)
            member.save()
            uf.save_m2m()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request, 'gitfabu/audit_manage.html', locals())


def task_observer(request):
    """写一个任务追踪模块，专门用于查看发布任务进度的，但是不能用于审核，只有查看的功能"""
    #fabu_tasks = my_request_task.objects.filter(table_name="git_deploy")
    fabu_tasks = my_request_task.objects.filter(loss_efficacy=False, isend=False)
    # 去除重复的审核人
    return render(request, 'gitfabu/task_observer.html', locals())


@login_required
def vue_manniu_list(request):
    data_huidu = git_deploy.objects.filter(platform="VUE蛮牛", classify="huidu", isops=True, islog=True)
    data_online = git_deploy.objects.filter(platform="VUE蛮牛", classify="online", isops=True, islog=True)
    data_test = git_deploy.objects.filter(platform="VUE蛮牛", classify="test", isops=True, islog=True)
    return render(request, 'gitfabu/vue_manniu_list.html', locals())


@login_required
def vue_pc_batch_update(request, env):
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"
    base_export_dir = "/data/manniuvue/" + classify + "/export/"
    platform = "VUE蛮牛"

    if request.method == 'POST':
        check_list = request.POST.getlist('check_list')
        if not check_list:
            return JsonResponse({'res': "Faild"}, safe=False)
        name = platform + "-" + classify + "_PC_批量更新"
        memo = {}
        for i in check_list:
            memo[i.split()[0]] = i.split()[1]
        print memo
        # 设计一下types,非常有用(平台-环境-方式-方法),此字段限制64字符
        types = '%s-%s-batch-vue_pc' % (platform, classify)
        mydata = my_request_task(name=name, types=types, table_name="git_code_update", uuid=uuid.uuid4(), memo=memo, initiator=request.user, status="审核中")
        mydata.save()
        auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=classify, isurgent=False, name="更新")
        if classify == "test":
            mydata.status = "通过审核，更新中"
            mydata.save()
            reslut = git_batch_update_task.delay(mydata.id, platform=platform, memos=memo)
        else:
            send_message_task.delay(mydata.id, auditor.id)
        return JsonResponse({'res': "OK"}, safe=False)

    data = git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True)
    cmd = "git log -n 1 --oneline"
    siteid_version = OrderedDict()
    for x in data:
        if x.islock:
            siteid_version[x.name] = "Locked"
        else:
            path = base_export_dir + x.name + "_pc"
            pull = subprocess.Popen(["git", "pull", "origin", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            #pull.wait()
            child = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            out, error = [i.decode("utf-8") for i in child.communicate()]
            siteid_version[x.name] = out
    return render(request, 'gitfabu/vue_pc_batch_update.html', locals())


@login_required
def vue_wap_batch_update(request, env):
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"
    base_export_dir = "/data/manniuvue/" + classify + "/export/"
    platform = "VUE蛮牛"

    if request.method == 'POST':
        check_list = request.POST.getlist('check_list')
        if not check_list:
            return JsonResponse({'res': "Faild"}, safe=False)
        name = platform + "-" + classify + "_WAP_批量更新"
        memo = {}
        for i in check_list:
            memo[i.split()[0]] = i.split()[1]
        print memo
        # 设计一下types,非常有用(平台-环境-方式-方法),此字段限制64字符
        types = '%s-%s-batch-vue_wap' % (platform, classify)
        mydata = my_request_task(name=name, types=types, table_name="git_code_update", uuid=uuid.uuid4(), memo=memo, initiator=request.user, status="审核中")
        mydata.save()
        auditor = git_deploy_audit.objects.get(platform="蛮牛", classify=classify, isurgent=False, name="更新")
        if classify == "test":
            mydata.status = "通过审核，更新中"
            mydata.save()
            reslut = git_batch_update_task.delay(mydata.id, platform=platform, memos=memo)
        else:
            send_message_task.delay(mydata.id, auditor.id)
        return JsonResponse({'res': "OK"}, safe=False)
    data = git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True).order_by('name')
    cmd = "git log -n 1 --oneline"
    siteid_version = OrderedDict()
    for x in data:
        if x.islock:
            siteid_version[x.name] = "Locked"
        else:
            path = base_export_dir + x.name + "_wap"
            pull = subprocess.Popen(["git", "pull", "origin", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            #pull.wait()
            child = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            out, error = [i.decode("utf-8") for i in child.communicate()]
            siteid_version[x.name] = out
    return render(request, 'gitfabu/vue_wap_batch_update.html', locals())


@login_required
def money_web_batch_update(request, env):
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"

    base_export_dir = "/data/moneyweb/" + classify + "/export/"
    platform = "现金网"
    if request.method == 'POST':
        check_list = request.POST.getlist('check_list')
        if not check_list: return JsonResponse({'res':"Faild"},safe=False)
        name = platform+"-"+classify+"_WEB_批量更新"
        memo={}
        for i in check_list:
            memo[i.split()[0]] = i.split()[1]
        print memo
        #设计一下types,非常有用(平台-环境-方式-方法),此字段限制64字符
        types='%s-%s-batch-web'% (platform,classify)
        mydata = my_request_task(name=name,types=types,table_name="git_code_update",uuid=uuid.uuid4(),memo=memo,initiator=request.user,status="审核中")
        mydata.save()
        if classify == "test":
            mydata.status="通过审核，更新中"
            mydata.save()
            reslut = git_batch_update_task.delay(mydata.id,platform=platform,memos=memo)
        else:
            auditor = git_deploy_audit.objects.get(platform="现金网",classify=classify,isurgent=False,name="更新")
            send_message_task.delay(mydata.id,auditor.id)
        return JsonResponse({'res':"OK"},safe=False)
    data = git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True).order_by('name')
    cmd = "git log -n 1 --oneline"
    siteid_version = OrderedDict()
    for x in data:
        if x.islock:
            siteid_version[x.name] = "Locked"
        else:
            path = base_export_dir + x.name
            pull = subprocess.Popen(["git", "pull", "origin", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            #pull.wait()
            child = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            out, error = [i.decode("utf-8") for i in child.communicate()]
            siteid_version[x.name] = out
    return render(request, 'gitfabu/money_web_batch_update.html', locals())


@login_required
def money_pc_batch_update(request, env):
    if "online" in env:
        classify = "online"
    elif "huidu" in env:
        classify = "huidu"
    elif "test" in env:
        classify = "test"
    platform = "现金网"
    base_export_dir = "/data/moneyweb/" + classify + "/export/"

    if request.method == 'POST':
        check_list = request.POST.getlist('check_list')
        if not check_list: return JsonResponse({'res':"Faild"},safe=False)
        name = platform+"-"+classify+"_PC_批量更新"
        memo={}
        for i in check_list:
            memo[i.split()[0]] = i.split()[1]
        print memo
        #设计一下types,非常有用(平台-环境-方式-方法),此字段限制64字符
        types='%s-%s-batch-js_pc'% (platform,classify)
        mydata = my_request_task(name=name,types=types,table_name="git_code_update",uuid=uuid.uuid4(),memo=memo,initiator=request.user,status="审核中")
        mydata.save()
        if classify == "test":
            mydata.status="通过审核，更新中"
            mydata.save()
            reslut = git_batch_update_task.delay(mydata.id,platform=platform,memos=memo)
        else:
            auditor = git_deploy_audit.objects.get(platform="现金网",classify=classify,isurgent=False,name="更新")
            send_message_task.delay(mydata.id,auditor.id)
        return JsonResponse({'res':"OK"},safe=False)

    data = git_deploy.objects.filter(platform=platform, classify=classify, isops=True, islog=True).order_by('name')
    cmd = "git log -n 1 --oneline"
    siteid_version = OrderedDict()
    for x in data:
        if x.islock:
            siteid_version[x.name] = "Locked"
        else:
            path = base_export_dir + x.name + "_js_pc"
            pull = subprocess.Popen(["git", "pull", "origin", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            #pull.wait()
            child = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            out, error = [i.decode("utf-8") for i in child.communicate()]
            siteid_version[x.name] = out



    return render(request, 'gitfabu/money_pc_batch_update.html', locals())

@login_required
def conf_admin(request):
    vue_data=git_deploy.objects.filter(platform="VUE蛮牛")
    money_data=git_deploy.objects.filter(platform="现金网")
    only_data=git_deploy.objects.filter(platform="单个项目")
    return render(request, 'gitfabu/conf_admin.html', locals())

@login_required
def deploy_servers(request, id):
    data = git_deploy.objects.get(pk=id)
    obj = data.server
    if request.method == 'POST':
        hosts=request.POST.get('hosts')
        work_path=request.POST.get('work_path')
        owner=request.POST.get('owner')
        rsync_exclude=request.POST.get('rsync_exclude')
        rsync_command=request.POST.get('rsync_command')
        last_command=request.POST.get('last_command')
        hosts=hosts.replace(" ","\r\n")
        obj.remoteip=hosts
        obj.remotedir=work_path
        obj.owner=owner
        obj.exclude=rsync_exclude
        obj.rsync_command=rsync_command
        obj.last_command=last_command
        obj.save()
        return JsonResponse({'res':"OK"},safe=False)
    return render(request, 'gitfabu/deploy_servers.html', locals())

@login_required
def deploy_gitrepo(request, id):
    data = git_deploy.objects.get(pk=id)
    if data.platform == "现金网":
        web_git = git_coderepo.objects.get(title=data.name, platform=data.platform, classify=data.classify)

        js_mobile_git = git_coderepo.objects.get(title="js_mobile", platform=data.platform, classify=data.classify)
        js_pc_git = git_coderepo.objects.get(title="js_pc", platform=data.platform, classify=data.classify)
        php_mobile_git = git_coderepo.objects.get(title="php_mobile", platform=data.platform, classify=data.classify)
        php_pc_git = git_coderepo.objects.get(title="php_pc", platform=data.platform, classify=data.classify)
        try:
            conf_git = git_coderepo.objects.get(title=data.name + "_config", platform=data.platform, classify=data.classify)
            git_list = [web_git.address, conf_git.address, js_mobile_git.address, js_pc_git.address, php_mobile_git.address, php_pc_git.address]
        except:
            git_list = [web_git.address, js_mobile_git.address, js_pc_git.address, php_mobile_git.address, php_pc_git.address]
        print git_list
        print js_mobile_git.address
    elif data.platform == "VUE蛮牛":
        conf_git = git_coderepo.objects.get(title="mn_config", platform=data.platform, classify=data.classify)
        php_git = git_coderepo.objects.get(title="mn_php", platform=data.platform, classify=data.classify)
        vue_pc_git = git_coderepo.objects.get(title=data.name + "vue_mn_pc", platform=data.platform, classify=data.classify)
        vue_wap_git = git_coderepo.objects.get(title=data.name + "vue_mn_wap", platform=data.platform, classify=data.classify)
        git_list = [conf_git.address, php_git.address, vue_pc_git.address, vue_wap_git.address]
    else:
        obj_git = git_coderepo.objects.get(title=data.name, platform=data.platform, classify=data.classify)
        git_list = [obj_git.address]
    return render(request, 'gitfabu/deploy_gitrepo.html', locals())

@login_required
def deploy_edit(request,id):
    data = git_deploy.objects.get(pk=id)
    if request.method == 'POST':
        is_log=request.POST.get('is_log')
        is_lock=request.POST.get('is_lock')
        if is_log == "yes":
            is_log=True
            print "项目为完成态"
        else:
            is_log=False
            print "项目未发布完成或失败"
        if is_lock == "yes":
            is_lock=True
            print "项目为挂起状态,有未完成更新"
        else:
            is_lock=False
            print "项目正常,可以更新"
        data.islog=is_log
        data.islock=is_lock
        data.save()
        return JsonResponse({'res':"OK"},safe=False)
    return render(request, 'gitfabu/deploy_edit.html', locals())

@login_required
def deploy_del(request,id):
    data = git_deploy.objects.get(pk=id)
    try:
        logs=data.deploy_logs.all()
        logs.delete()
    except:
        pass
    try:
        update_records=data.deploy_update.all()
        update_records.delete()
    except:
        pass
    data.delete()
    return JsonResponse({'res':"OK"},safe=False)