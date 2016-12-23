#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from automation.models import Tools, Confile, deploy
from automation.forms import ToolsForm, ConfileFrom, DeployForm
# Create your views here.
from api.git_api import Repo
from api.svn_api import Svnrepo
from api.common_api import check_file

import os.path
import shutil
import subprocess
import json
import time
from django.http import JsonResponse
from .tasks import deploy_use_ansible,go_back_ansible,svn_checkout_task,svn_update_log,svn_update_task
from tempfile import NamedTemporaryFile
from assets.models import Server
from celery.result import AsyncResult


@permission_required('automation.add_Tools', login_url='/auth_error/')
def tools_add(request):
    tf = ToolsForm()
    tf_errors = []
    data = Tools.objects.all()
    title = request.POST.get('title', '')
    url = request.POST.get('address', '')
    if Tools.objects.filter(title=title):
        tf_errors.append(u"所填标题已存在")
    if Tools.objects.filter(address=url):
        tf_errors.append(u"所填地址已存在")

    if request.method == 'POST':
        tf = ToolsForm(request.POST)
        if tf.is_valid():
            if not tf_errors:
                tf_data = tf.save()
            return HttpResponseRedirect('/success/')

    # return HttpResponse("success")
    return render(request,'automation/tools_add.html',locals())

@permission_required('automation.add_Tools', login_url='/auth_error/')
def tools_list(request):
    data = Tools.objects.all()
    return render(request,'automation/tools_list.html',locals())

@permission_required('automation.add_Tools', login_url='/auth_error/')
def tools_edit(request,uuid):
    data = Tools.objects.get(pk=uuid)
    tf = ToolsForm(instance=data)
    if request.method == 'POST':
        tf = ToolsForm(request.POST,instance=data)
        if tf.is_valid():
            tf_data = tf.save()
            return HttpResponseRedirect('/success/')

    return render(request,'automation/tools_edit.html',locals())

@permission_required('automation.delete_Tools', login_url='/auth_error/')
def tools_delete(request,uuid):
    data = get_object_or_404(Tools,uuid=uuid)
    if data:
        data.delete()
        return HttpResponse("success")
    
    return render(request,'automation/tools_list.html',locals())

@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_add(request):
    """实现添加发布的基本参数配置，但提交的时候会到指定的目录下面clone仓库"""
    cf = ConfileFrom()
    cf_errors = []
    name = request.POST.get('name', '')
    path = request.POST.get('localhost_dir', '')
    tool = request.POST.get('tool', '')
    if tool:
        tool = Tools.objects.get(uuid=tool)
        url = tool.address
    ifile = path + '.git/config'


    if Confile.objects.filter(name=name):
        cf_errors.append(u"所填标题已存在")
    # if Confile.objects.filter(localhost_dir=path):
    #     cf_errors.append(u"所填仓库路径已存在")


    if request.method == 'POST':
        cf = ConfileFrom(request.POST)
        if os.path.isfile(ifile):
            if check_file(ifile,url):
                pass
            else:
                cf_errors.append(u"所填仓库路径已存在,并且里面已经有git文件")
        if cf.is_valid():
            if not cf_errors:
                cf_data = cf.save()            ##保存信息后先判断repo的clone路径存不存在，不存在则创建
                if os.path.isdir(path):
                    pass
                else:
                    os.makedirs(path)
                repo = Repo(path)
                repo.git_clone(url,path)
                return HttpResponseRedirect('/deploy/conf_list/')

    return render(request,'automation/conf_add.html',locals())


@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_add_svn(request):
    """实现添加发布的基本参数配置，但提交的时候会到指定的目录下面clone仓库"""
    cf = ConfileFrom()
    cf_errors = []
    name = request.POST.get('name', '')

    path = request.POST.get('localhost_dir', '')
    path_two = request.POST.get('localhost_dir_two', '')
    path_three = request.POST.get('localhost_dir_three', '')

    tool_tail = request.POST.get('tool_tail', '')
    tool_tail_two = request.POST.get('tool_tail_two', '')
    tool_tail_three = request.POST.get('tool_tail_three', '')


    svn_options = Tools.objects.filter(name='Subversion')

    if Confile.objects.filter(name=name):
        cf_errors.append(u"所填标题已存在")
    if Confile.objects.filter(localhost_dir=path):
        cf_errors.append(u"所填主库checkout目录已存在")


    if request.method == 'POST':
        cf = ConfileFrom(request.POST)
        tool_uuid = request.POST.get('tool', '')
        data = Tools.objects.get(pk=tool_uuid)
        svn_url = data.address + tool_tail

        tool_uuid_two = request.POST.get('tool_two', '')
        svn_url_two = None
        if tool_uuid_two:
            data_two = Tools.objects.get(pk=tool_uuid_two)
            svn_url_two = data_two.address + tool_tail_two
        if svn_url_two:
            if not path_two:
                cf_errors.append(u"没有给出副库checkout的目录")

        tool_uuid_three = request.POST.get('tool_three', '')
        svn_url_three = None
        if tool_uuid_three:
            data_three = Tools.objects.get(pk=tool_uuid_three)
            svn_url_three = data_three.address + tool_tail_three
        if svn_url_three:
            if not path_three:
                cf_errors.append(u"没有给出叁库checkout的目录")

        if cf.is_valid():
            if not cf_errors:
                cf_data = cf.save()            ##保存信息
                if svn_url:
                    user = data.user
                    password = data.passwd
                    if os.path.isdir(path):
                        pass
                    else:
                        os.makedirs(path)
                    job = svn_checkout_task.delay(user,password,svn_url,path,"--no-auth-cache")
                    # repo = Svnrepo(path)               ## checkout第一个库
                    # repo.svn_checkout(user,password,svn_url,path,"--no-auth-cache")

                if svn_url_two:
                    user_two = data_two.user
                    password_two = data_two.passwd
                    if os.path.isdir(path_two):
                        pass
                    else:
                        os.makedirs(path_two)
                    job = svn_checkout_task.delay(user_two,password_two,svn_url_two,path_two,"--no-auth-cache")
                    # repo_two = Svnrepo(path_two)
                    # repo.svn_checkout(user_two,password_two,svn_url_two,path_two,"--no-auth-cache")

                if svn_url_three:
                    user_three = data_three.user
                    password_three = data_three.passwd
                    if os.path.isdir(path_three):
                        pass
                    else:
                        os.makedirs(path_three)
                    job = svn_checkout_task.delay(user_three,password_three,svn_url_three,path_three,"--no-auth-cache")
                    # repo_three = Svnrepo(path_three)
                    # repo.svn_checkout(user_three,password_three,svn_url_three,path_three,"--no-auth-cache")


            return HttpResponseRedirect('/deploy/conf_list/')

    # return HttpResponse("success")
    return render(request,'automation/conf_add_svn.html',locals())


@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_list(request):
    data = Confile.objects.all()
    return render(request,'automation/conf_list.html',locals())

@permission_required('automation.delete_Confile', login_url='/auth_error/')
def conf_delete(request,uuid):
    data = get_object_or_404(Confile,uuid=uuid)
    if data:
        data.delete()
        return HttpResponse("SUCCESS!")
    return render(request,'automation/deploy_business.html',locals())

@permission_required('automation.change_Confile', login_url='/auth_error/')
def conf_edit(request,uuid):
    data = Confile.objects.get(pk=uuid)
    cf = ConfileFrom(instance=data)
    if request.method == 'POST':
        cf = ConfileFrom(request.POST,instance=data)
        if cf.is_valid():
            cf_data = cf.save()
            return HttpResponseRedirect('/success/')

    return render(request,'automation/conf_edit.html',locals())

@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_detail(request,uuid):
    data = Confile.objects.get(pk=uuid)
    if data:
        cf = ConfileFrom(instance=data)
    return render(request,'automation/conf_detail.html',locals())

@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_copy(request,uuid):
    data = Confile.objects.get(pk=uuid)
    data.save()
    name = data.name + "- copy"
    if data:
        new_data = data
        new_data.pk = None
        new_data.name = name
        new_data.save()
    return HttpResponse("copy model success!")


@permission_required('automation.add_Confile', login_url='/auth_error/')
def conf_check(request,uuid):
    data = Confile.objects.get(pk=uuid)
    git_addr = data.tool.address
    path = data.localhost_dir
    # num = data.max_number
    repo = Repo("/tmp/etc/murphy")
    bb = repo.git_all_branch()         #获取所有的分支信息
    # commit = repo.git_log(limit=num,template="--pretty=oneline")   #获取当前分支的log
    # log = repo.git_log()
    show = repo.git_show_tag("/tmp/etc/murphy",release="v-1.0.3").split()[1]

    return HttpResponse(show[0:8])


    #return render(request,'automation/conf_check.html',locals())




@permission_required('automation.add_deploy', login_url='/auth_error/')
def deploy_business(request):
    data = Confile.objects.all()
    return render(request,'automation/deploy_business.html',locals())

@permission_required('automation.add_deploy', login_url='/auth_error/')
def deploy_add(request,uuid):
    data = Confile.objects.get(pk=uuid)
    sit_id = data.business.nic_name
    path = data.localhost_dir
    repo = Repo(path)
    repo.git_checkout("master")          ##git pull --all之前一定要git checkout master
    pull = repo.git_pull(source="all")  ##在分支上先执行pull，更新到最新的仓库数据，相当于git pull --all
    branch = repo.git_all_branch()    ##拉取所有的分支信息，分支下面的commit_id是使用ajax获取
    tags = repo.git_tags()            ##拉取所有的tag信息

    now = int(time.time())
    ctime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

    df = DeployForm()
    df_errors = []

    if request.method == 'POST':
        if 'formtag' in request.POST:
            name = request.POST.get('tag_name','')
            tag = request.POST.get('tag','')
            memo = request.POST.get('tag_memo','')
            branches = "master"
            show = repo.git_show_tag(path,release=tag).split()[1]
            release = show[0:8]
            executive_user = request.user
            confile = data
            check_conf = "pass"
            status = u"未发布"
            tag_data = deploy(ctime=ctime,name=name,sit_id=sit_id,branches=branches,release=release,executive_user=executive_user,
                confile=confile,check_conf=check_conf,status=status,tag=tag,memo=memo,execution_time=now,exist=False)
            tag_data.save()
            return HttpResponseRedirect('/deploy/deploy_list/')

        elif 'formbranch' in request.POST:
            name = request.POST.get('branch_name','')
            branches = request.POST.get('branches','')
            release = request.POST.get('release','')[0:8]
            executive_user = request.user
            confile = data
            check_conf = "pass"
            status = u"未发布"
            tag = ''
            memo = request.POST.get('branch_memo','')
            branch_data = deploy(ctime=ctime,name=name,sit_id=sit_id,branches=branches,release=release,executive_user=executive_user,
                confile=confile,check_conf=check_conf,status=status,tag=tag,memo=memo,execution_time=now,exist=False)
            branch_data.save()
            return HttpResponseRedirect('/deploy/deploy_list/')

    return render(request,'automation/deploy_add.html',locals())



@permission_required('automation.add_deploy', login_url='/auth_error/')
def deploy_branch_select(request):
    """这个函数定义如何获取仓库的commit_id，返回json数据给前端ajax"""
    branch = request.GET.get('branch','master')
    uuid = request.GET.get('uuid',0)
    data = Confile.objects.get(pk=uuid)
    path = data.localhost_dir
    num = data.max_number            ##这一项可以控制显示的commit_id的条数，但是要在git_log的limit参数中设置num，默认是10
    repo = Repo(path)
    change_branch = repo.git_checkout(branch)      ##切换到所选的分支上面
    pull = repo.git_pull(source="all")             ##在分支上先执行pull，更新到最新的仓库数据，相当于git pull --all
    commitid = repo.git_log(limit='10',template="--pretty=oneline")       ##在分支上面查看commit_id

    return JsonResponse(commitid,safe=False)

@permission_required('automation.add_deploy', login_url='/auth_error/')
def deploy_list(request):
    data = deploy.objects.all()
    user = request.user

    if user.is_superuser:
        deploy_list = data
    else:
        deploy_list = data.filter(executive_user=user)
    # return HttpResponse(user.is_superuser)

    return render(request,'automation/deploy_list.html',locals())


def create_inventory(uuid,groupname):
    hostsFile = NamedTemporaryFile(delete=False)
    data = Confile.objects.get(pk=uuid)
    group = "[%s]" % groupname
    L = [group]
    for i in [x for x in data.server_list.split('\r\n') if x]:
        i = Server.objects.get(ssh_host=i)
        host = "%s ansible_ssh_port=%s ansible_ssh_use=root ansible_ssh_pass=%s" % (i.ssh_host,i.ssh_port,i.ssh_password)
        L.append(host)
    for s in L:
        hostsFile.write(s+'\n')
    hostsFile.close()
    return hostsFile.name

@permission_required('automation.delete_deploy', login_url='/auth_error/')
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

@permission_required('automation.delete_deploy', login_url='/auth_error/')
def deploy_online(request,uuid):
    data = get_object_or_404(deploy,pk=uuid)
    conf_data = data.confile
    max_number = conf_data.max_number
    branch = data.branches
    commit_id = data.release
    repo_path = conf_data.localhost_dir      ##这里需要做一个有没有repo clone的判断
    specific_path = conf_data.specific       ## 指定文件需要判断是否存在
    repo = Repo(repo_path)
    change_branch = repo.git_checkout("master")   ##切换到分支上面
    pull = repo.git_pull(source="all")          ##更新所有的分支
    if request.method == 'POST':
        ##step1 切换分支并切换到具体版本
        if data.tag:
            change_version = repo.git_checkout(data.tag)
        else:
            change_version = repo.git_checkout(commit_id)
        ##step2 删除临时目录，因为下面cpoy代码的时候，目录不能存在，不然在这里应该要创建临时目录的
        path = '/tmp' + repo_path
        if os.path.isdir(path):
            shutil.rmtree(path)      ##如果目录存在就删除


        ##step3 代码拷贝到临时目录前需要执行的动作
        pre_deploy = conf_data.pre_deploy
        Lpre = [a for a in pre_deploy.split('\r\n') if a]
        for i in Lpre:
            res = subprocess.Popen(i,shell=True)
        ##step4 将代码拷贝到临时目录
        ignores = conf_data.exclude
        L = [a for a in ignores.split('\r\n') if a]
        src = repo_path
        dst = path

        if specific_path:
            src = src + specific_path
            if os.path.isfile(src):
                os.makedirs(dst)
                shutil.copy(src,dst)
            else:
                shutil.copytree(src,dst,ignore=shutil.ignore_patterns(*L))
        else:
            shutil.copytree(src,dst,ignore=shutil.ignore_patterns(*L))

        ##step5 代码拷贝到临时目录后需要执行的一些动作
        post_deploy = conf_data.post_deploy
        Lpost = [a for a in post_deploy.split('\r\n') if a]
        for i in Lpost:
            res = subprocess.Popen(i,shell=True)
        ##step6 更新发布状态为已发布，更新发布时间，更新exist状态，将远程服务器上要删掉的commitid找出来，传给ansible
        now = int(time.time())
        deploy.objects.filter(confile=conf_data).filter(status=u'已发布-使用中').update(status=u'已发布')
        deploy.objects.filter(confile=conf_data).filter(status=u'已回滚-使用中').update(status=u'已发布')

        deploy.objects.filter(pk=uuid).update(status=u'已发布-使用中',execution_time=now,exist=True)

        alldata = deploy.objects.filter(confile=conf_data).filter(exist=True)
        exist_num = alldata.count()
        if int(exist_num) >= int(max_number):
            Lexist = [a.execution_time for a in alldata if a]
            a = min(Lexist)
            deploy.objects.filter(confile=conf_data).filter(execution_time=a).update(exist=False)
            expire_commit =  deploy.objects.get(execution_time=a).release
            msg = u"远程主机过期版本号为：%s" % expire_commit
        else:
            expire_commit = '123456789'   ## 如果有过期版本就删除，如果没有，为了防止误删，给过期的版本赋值为123456789
        ##step7-8-9 使用ansible将本地主机上的代码传送至远程服务器，并执行pre和post动作
        groupname = "deploy_group"
        inventory = create_inventory(conf_data.uuid,groupname)         #发布远程服务器必须要在资产列表里面有，不然会报错
        play_book = '/etc/ansible/rsync.yml'
        tmp_dir = path
        webroot_user = conf_data.webroot_user
        webroot = conf_data.webroot
        release_dir = conf_data.relaese_dir
        commit_id = commit_id
        pre_release_ob = conf_data.pre_release
        pre_release_list = [a for a in pre_release_ob.split('\r\n') if a]
        pre_release = " && ".join(pre_release_list)
        post_release_ob = conf_data.post_release
        post_release_list = [a for a in post_release_ob.split('\r\n') if a]
        post_release = " && ".join(post_release_list)

        job = deploy_use_ansible.delay(inventory,play_book,tmp_dir,webroot_user,webroot,release_dir,commit_id,expire_commit,pre_release,post_release,groupname)
        if job: 
            task_id = job.id

    return render(request,'automation/deploy_online.html',locals())


@permission_required('automation.delete_deploy', login_url='/auth_error/')
def go_back(request,uuid):
    deploy_data = get_object_or_404(deploy,pk=uuid)
    config_data = deploy_data.confile
    groupname = "deploy_go_back"
    inventory = create_inventory(config_data.uuid,groupname)
    play_book = '/etc/ansible/deploy_go_back.yml'
    pre_release_ob = config_data.pre_release
    pre_release_list = [a for a in pre_release_ob.split('\r\n') if a]
    pre_release = " && ".join(pre_release_list)
    post_release_ob = config_data.post_release
    post_release_list = [a for a in post_release_ob.split('\r\n') if a]
    post_release = " && ".join(post_release_list)
    if deploy_data.confile.tool.name == "GIT":
        goback_release = deploy_data.release
    else:
        goback_release = deploy_data.sit_id + deploy_data.release

    job = go_back_ansible.delay(inventory,play_book,groupname,config_data.webroot_user,config_data.webroot,config_data.relaese_dir,goback_release,pre_release,post_release)
    if job:
        task_id = job.id
    now = int(time.time())
    deploy.objects.filter(confile=config_data).filter(status=u'已发布-使用中').update(status=u'已发布')
    deploy.objects.filter(confile=config_data).filter(status=u'已回滚-使用中').update(status=u'已发布')

    deploy.objects.filter(pk=uuid).update(status=u'已回滚-使用中',execution_time=now,exist=True)

    return HttpResponseRedirect('/success/')

@permission_required('automation.add_deploy', login_url='/auth_error/')
def deploy_add_svn(request,uuid):
    df_errors = []
    data = Confile.objects.get(pk=uuid)
    sit_id = data.business.nic_name

    if request.method == 'POST':
        now = int(time.time())
        ctime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        if 'formsvntag' in request.POST:
            name = request.POST.get('tag_name','')
            tag = request.POST.get('tag','')
            tag_two = request.POST.get('tag_two','')
            tag_three = request.POST.get('tag_three','')
            memo = request.POST.get('tag_memo','')
            branches = "master"
            release = tag.split('_')[0]
            release_two = tag_two.split('_')[0]
            release_three = tag_three.split('_')[0]
            executive_user = request.user
            confile = data
            check_conf = "pass"
            status = u"未发布"
            tag_data = deploy(ctime=ctime,name=name,sit_id=sit_id,branches=branches,release=release,release_two=release_two,release_three=release_three,executive_user=executive_user,
                confile=confile,check_conf=check_conf,status=status,tag=tag,tag_two=tag_two,tag_three=tag_three,memo=memo,execution_time=now,exist=False)
            tag_data.save()
            return HttpResponseRedirect('/deploy/deploy_list/')
    else:
        path = data.localhost_dir
        user = data.tool.user
        password = data.tool.passwd
        limit = data.max_number
        job = svn_update_log.delay(user,password,path,str(limit),"/tmp/svn_one_log","--no-auth-cache")
        job_result = job.get()

        data_two = data.tool_two
        if data_two:
            user_two = data_two.user
            password_two = data_two.passwd
            path_two = data.localhost_dir_two
            job_two = svn_update_log.delay(user_two,password_two,path_two,str(limit),"/tmp/svn_two_log","--no-auth-cache")
            job_two_result = job_two.get()


        data_three = data.tool_three
        if data_three:
            user_three = data_three.user
            password_three = data_three.passwd
            path_three = data.localhost_dir_three
            job_three = svn_update_log.delay(user_three,password_three,path_three,str(limit),"/tmp/svn_three_log","--no-auth-cache")
            job_three_result = job_three.get()

    return render(request,'automation/deploy_add_svn.html',locals())

@permission_required('automation.delete_deploy', login_url='/auth_error/')
def deploy_online_svn(request,uuid):
    data = get_object_or_404(deploy,pk=uuid)
    conf_data = data.confile
    max_number = conf_data.max_number
    branch = data.branches
    commit_id = data.release
    commit_id_two = data.release_two
    commit_id_three = data.release_three

    repo_path = conf_data.localhost_dir
    repo_path_two = conf_data.localhost_dir_two
    repo_path_three = conf_data.localhost_dir_three

    user = conf_data.tool.user
    password = conf_data.tool.passwd
    # svn_update_task.delay(user,password,repo_path,"all","--no-auth-cache")    ## 更新所有svn库到最新版本,吃完饭后要写切换到具体版本的code
    svn_update_task.delay(user,password,repo_path,commit_id,"--no-auth-cache")
    if repo_path_two: 
        user_two = conf_data.tool_two.user
        password_two = conf_data.tool_two.passwd
        # svn_update_task.delay(user_two,password_two,repo_path_two,"all","--no-auth-cache")
        svn_update_task.delay(user_two,password_two,repo_path_two,commit_id_two,"--no-auth-cache")


    if repo_path_three: 
        user_three = conf_data.tool_three.user
        password_three = conf_data.tool_three.passwd
        # svn_update_task.delay(user_three,password_three,repo_path_three,"all","--no-auth-cache")
        svn_update_task.delay(user_three,password_three,repo_path_three,commit_id_three,"--no-auth-cache")


    if request.method == 'POST':
        ##step1 切换分支并切换到具体版本,上面的代码已经解决了此步骤
        ##step2 删除临时目录，因为下面cpoy代码的时候，目录不能存在，不然在这里应该要创建临时目录的
        path = '/tmp/' + data.sit_id + commit_id
        if os.path.isdir(path):
            shutil.rmtree(str(path))      ##如果目录存在就删除

        ##step3 代码拷贝到临时目录前需要执行的动作
        pre_deploy = conf_data.pre_deploy
        Lpre = [a for a in pre_deploy.split('\r\n') if a]
        for i in Lpre:
            res = subprocess.Popen(i,shell=True)
        ##step4 将代码拷贝到临时目录
        ignores = conf_data.exclude
        L = [a for a in ignores.split('/r/n') if a]
        print L
        src = repo_path
        dst = path
        shutil.copytree(str(src),str(dst),ignore=shutil.ignore_patterns(*L))
        ##step5 代码拷贝到临时目录后需要执行的一些动作
        post_deploy = conf_data.post_deploy
        Lpost = [a for a in post_deploy.split('\r\n') if a]
        for i in Lpost:
            res = subprocess.Popen(i,shell=True)
        ##step6 更新发布状态为已发布，更新发布时间，更新exist状态，将远程服务器上要删掉的commitid找出来，传给ansible
        now = int(time.time())
        deploy.objects.filter(confile=conf_data).filter(status=u'已发布-使用中').update(status=u'已发布')
        deploy.objects.filter(confile=conf_data).filter(status=u'已回滚-使用中').update(status=u'已发布')

        deploy.objects.filter(pk=uuid).update(status=u'已发布-使用中',execution_time=now,exist=True)

        alldata = deploy.objects.filter(confile=conf_data).filter(exist=True)
        exist_num = alldata.count()
        if int(exist_num) >= int(max_number):
            Lexist = [a.execution_time for a in alldata if a]
            a = min(Lexist)
            deploy.objects.filter(confile=conf_data).filter(execution_time=a).update(exist=False)
            expire_commit =  deploy.objects.get(execution_time=a).release
            expire_commit = deploy.objects.get(execution_time=a).sit_id + expire_commit
            msg = u"远程主机过期版本号为：%s" % expire_commit
        else:
            expire_commit = '123456789'   ## 如果有过期版本就删除，如果没有，为了防止误删，给过期的版本赋值为123456789
        print expire_commit
        ##step7-8-9 使用ansible将本地主机上的代码传送至远程服务器，并执行pre和post动作
        groupname = "deploy_group"
        inventory = create_inventory(conf_data.uuid,groupname)         #发布远程服务器必须要在资产列表里面有，不然会报错
        play_book = '/etc/ansible/rsync.yml'
        tmp_dir = path
        webroot_user = conf_data.webroot_user
        webroot = conf_data.webroot
        release_dir = conf_data.relaese_dir
        commit_id = data.sit_id + commit_id
        pre_release_ob = conf_data.pre_release
        pre_release_list = [a for a in pre_release_ob.split('\r\n') if a]
        pre_release = " && ".join(pre_release_list)
        post_release_ob = conf_data.post_release
        post_release_list = [a for a in post_release_ob.split('\r\n') if a]
        post_release = " && ".join(post_release_list)

        job = deploy_use_ansible.delay(inventory,play_book,tmp_dir,webroot_user,webroot,release_dir,commit_id,expire_commit,pre_release,post_release,groupname)
        if job: 
            task_id = job.id

    return render(request,'automation/deploy_online_svn.html',locals())