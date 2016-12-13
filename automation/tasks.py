#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex_deploy
import os
from api.svn_api import Svnrepo

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

