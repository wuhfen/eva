#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
from api.ansible_api import ansiblex_deploy
import os


@shared_task()
def deploy_use_ansible(inventory,play_book,tmp_dir,webroot_user,webroot,release_dir,commit_id,expire_commit,pre_release,post_release,groupname):

    current_task.update_state(state="PROGRESS")
    ansiblex_deploy(vars1=inventory,vars2=play_book,vars3=tmp_dir,vars4=webroot_user,vars5=webroot,vars6=release_dir,vars7=commit_id,vars8=expire_commit,vars9=pre_release,vars10=post_release,vars11=groupname)
    os.remove(inventory)
    return "200"


