#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex_deploy,MyTask
import os
from api.svn_api import Svnrepo
from api.ssh_api import ssh_cmd
from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
import time
from time import sleep
from automation.models import scriptdeploy,scriptlog,gengxin_deploy,gengxin_code
import subprocess
from assets.models import Server
from automation.gengxin_deploy import website_deploy

@shared_task()
def deploy_use_ansible(inventory,play_book,tmp_dir,webroot_user,webroot,release_dir,commit_id,expire_commit,pre_release,post_release,groupname):

    current_task.update_state(state="PROGRESS")
    ansiblex_deploy(vars1=inventory,vars2=play_book,vars3=tmp_dir,vars4=webroot_user,vars5=webroot,vars6=release_dir,vars7=commit_id,vars8=expire_commit,vars9=pre_release,vars10=post_release,vars11=groupname)
    os.remove(inventory)
    return "200"


@shared_task()
def go_back_ansible(inventory,play_book,groupname,webroot_user,webroot,relaese_dir,release,pre_release,post_release):
    ansiblex_deploy(vars1=inventory,vars2=play_book,vars3=groupname,vars4=webroot_user,vars5=webroot,vars6=relaese_dir,vars7=release,vars8=pre_release,vars9=post_release)
    os.remove(inventory)
    return "200"

@shared_task()
def svn_checkout_task(user,password,url,path,*args):
    current_task.update_state(state="PROGRESS")
    repo = Svnrepo(path,user,password)
    repo.svn_checkout(url,path,*args)
    return "svn_add_conf_200"


@shared_task()
def svn_checkout_and_mergen_task(obj_dict,merge_command,*args):
    current_task.update_state(state="PROGRESS")
    for i in obj_dict:
        path = i['exportdir']
        user = i['username']
        password = i['password']
        url = i['repo']
        repo = Svnrepo(path,user,password)
        repo.svn_checkout(url,path,*args)
    p = subprocess.Popen(merge_command, shell=True, stdout=subprocess.PIPE)
    res = p.stdout.readlines()
    print res
    return "svn_add_conf_and_mergen_200"

@shared_task()
def gengxin_code_edit_task(old_dict,new_dict,merge_command,*args):
    current_task.update_state(state="PROGRESS")
    old = []
    for i in old_dict:
        old.append(i['exportdir'])
    print old
    for i in new_dict:
        if i['exportdir'] not in old:
            genxin_code_dir(i['exportdir'])
            repo = Svnrepo(i['exportdir'],i['username'],i['password'])
            repo.svn_checkout(i['repo'],i['exportdir'],*args)
    sleep(1)
    p = subprocess.Popen(merge_command, shell=True, stdout=subprocess.PIPE)
    res = p.stdout.readlines()
    print res
    return "gengxin_code_edit_task_200"




@shared_task()
def svn_update_log(user,password,path,limit,logfile,*args):

    current_task.update_state(state="PROGRESS")
    repo = Svnrepo(path,user,password)
    repo.svn_update("all",*args)
    res = repo.svn_get_reversion(logfile,limit)
    return res

@shared_task()
def svn_update_task(user,password,path,reversion,*args):
    current_task.update_state(state="PROGRESS")
    repo = Svnrepo(path,user,password)
    res = repo.svn_update(reversion,*args)
    return res

@shared_task()
def script_update_task(uuid,host,command):
    current_task.update_state(state="PROGRESS")
    res = ssh_cmd(host,command)
    string = ""
    for i in res:
        string = string+i
    data = scriptdeploy.objects.get(pk=uuid)
    now = int(time.time())
    logdata = scriptlog(user=data.executive_user,name=data.name,memo=data.memo,command=command,result=string,sort_time=now,scriptdeploy=data)
    logdata.save()
    scriptdeploy.objects.filter(pk=uuid).update(status="已更新")
    return "123" 

@shared_task()
def gengxin_update_task(uuid,env):
    """给出版本信息，目录信息，源站，更新后变更任务状态为已更新"""
    current_task.update_state(state="PROGRESS")
    data = gengxin_deploy.objects.get(pk=uuid)
    siteid = data.siteid
    method = data.method
    pub_reversion = data.pub_reversion
    web_reversion = data.web_reversion
    if siteid == "all":
        conf_list = gengxin_code.objects.filter(classify=env)
        if method == "pa":
            for i in conf_list:
                my_siteid = i.business.nic_name
                print("public开始更新: %s 版本号：%s"% (my_siteid,pub_reversion))
                Mywd = website_deploy(env,my_siteid)
                Mywd.pub_export(pub_reversion)
                Mywd.merge_web(i.uuid)
                Mywd.ansible_rsync_web(i.remoteip,i.rsync_command,i.last_command,i.exclude)
        else:
            conf_list = gengxin_code.objects.filter(classify=env).filter(phone_site=True)
            for i in conf_list:
                if "f" in i.business.nic_name:
                    my_siteid = i.business.nic_name.replace('f','mf')
                else:
                    my_siteid = i.business.nic_name + 'm'
                print("public开始更新: %s 版本号：%s"% (my_siteid,pub_reversion))
                Mywd = website_deploy(env,my_siteid)
                Mywd.pub_export(pub_reversion)
                Mywd.merge_web(i.uuid)
                Mywd.ansible_rsync_web(i.remoteip,i.rsync_command,i.last_command,i.exclude)
    else:
        conf_data = data.code_conf
        Mywd = website_deploy(env,siteid)
        if method == "a":
            Mywd = website_deploy(env,siteid)
            Mywd.pub_export(pub_reversion)
            Mywd.web_export(web_reversion)
            # Mywd.conf_export()
        elif method == "pp":
            Mywd.pub_export(pub_reversion)
        else:
            Mywd.web_export(web_reversion)
        Mywd.merge_web(conf_data.uuid)
        Mywd.ansible_rsync_web(conf_data.remoteip,conf_data.rsync_command,conf_data.last_command,conf_data.exclude)
    data.status = "已更新"
    now = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    data.execution_time = now
    data.save()
    return "website code update accomplish"

@shared_task()
def fabu_update_task(uuid):
    current_task.update_state(state="PROGRESS")
    tf_data = gengxin_code.objects.get(pk=uuid)
    print "开始发布%s"% tf_data.business.nic_name

    if tf_data.phone_site:
        if "f" in tf_data.business.nic_name:
            siteid = tf_data.business.nic_name.replace("f","mf")
        else:
            siteid = tf_data.business.nic_name+'m'
        MyPhone = website_deploy(tf_data.classify,siteid,method="fabu")
    MyWeb = website_deploy(tf_data.classify,tf_data.business.nic_name,method="fabu")
    MyWeb.merge_web(tf_data.uuid)
    MyWeb.ansible_rsync_web(tf_data.remoteip,tf_data.rsync_command,tf_data.last_command,tf_data.exclude)
    print "已完成发布%s"% tf_data.business.nic_name
    return "website pull code and rsync it to remote_server accomplish"

@shared_task()
def fabu_nginxconf_task(uuid,choice=None):
    current_task.update_state(state="PROGRESS")
    tf_data = gengxin_code.objects.get(pk=uuid)
    MyWeb = website_deploy(tf_data.classify,tf_data.business.nic_name)
    print "开始网站的域名配置"
    if not choice:
        print "发布新站，配置网站域名，ag域名，后台域名"
        MyWeb.web_front_domain(tf_data.front_domain,tf_data.remoteip,"front",isphone=tf_data.phone_site)
        MyWeb.web_front_domain(tf_data.agent_domain,tf_data.remoteip,"agent")
        MyWeb.web_front_domain(tf_data.backend_domain,tf_data.remoteip,"backend")
    else:
        if choice == "front":
            print "更新网站域名"
            MyWeb.web_front_domain(tf_data.front_domain,tf_data.remoteip,"front",isphone=tf_data.phone_site)
        elif choice == "agent":
            print "更新ag域名"
            MyWeb.web_front_domain(tf_data.agent_domain,tf_data.remoteip,"agent")
        else:
            print "更新后台ds168域名"
            MyWeb.web_front_domain(tf_data.backend_domain,tf_data.remoteip,"backend")
    print "域名配置完成"
    return "website configurate nginx accomplish"



