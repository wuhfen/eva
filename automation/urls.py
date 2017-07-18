#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from automation import views
from automation.version import applys as aviews

from automation import script_deploy as sviews
from automation import gengxin as gviews


urlpatterns = [
#"""产品线增删查改"""
    url(r'^tools_add/$', views.tools_add, name="tools_add"),
    url(r'^tools_list/$', views.tools_list, name="tools_list"),
    url(r'^tools_edit/(?P<uuid>[^/]+)/$', views.tools_edit, name="tools_edit"),
    url(r'^tools_delete/(?P<uuid>[^/]+)/$', views.tools_delete, name='tools_delete'),

#"""产品线增删查改"""
    url(r'^conf_add/$', views.conf_add, name="conf_add"),
    url(r'^conf_list/$', views.conf_list, name="conf_list"),
    url(r'^conf_edit/(?P<uuid>[^/]+)/$', views.conf_edit, name="conf_edit"),
    url(r'^conf_delete/(?P<uuid>[^/]+)/$', views.conf_delete, name='conf_delete'),
    url(r'^conf_detail/(?P<uuid>[^/]+)/$', views.conf_detail, name='conf_detail'),
    url(r'^conf_copy/(?P<uuid>[^/]+)/$', views.conf_copy, name='conf_copy'),
    url(r'^conf_check/(?P<uuid>[^/]+)/$', views.conf_check, name='conf_check'),
    # url(r'^conf_check/$', views.conf_check, name='conf_check'),
    url(r'^conf_add_svn/$', views.conf_add_svn, name="conf_add_svn"),



#开发人员申请发布更新
    url(r'^version/update/$', aviews.version_update, name="version_update"),
    url(r'^version/update/pulldata/(?P<choice>[^/]+)/$', aviews.pull_data, name="pull_data"),
    url(r'^version/update/savedata/$', aviews.save_data, name="save_data"),
    url(r'^version/update/showbar/(?P<uuid>[^/]+)/$', aviews.update_online_release, name="update_online_release"),
    url(r'^version/update/abolish/(?P<uuid>[^/]+)/$', aviews.abolish_release, name="abolish_release"),
    url(r'^version/update/showlog/(?P<uuid>[^/]+)/$', aviews.update_online_catlog, name="update_online_catlog"),



#"""申请发布"""
    url(r'^deploy_business/$', views.deploy_business, name="deploy_business"),
    url(r'^deploy_list/$', views.deploy_list, name="deploy_list"),
    url(r'^deploy_add/(?P<uuid>[^/]+)/$', views.deploy_add, name="deploy_add"),
    url(r'^deploy_online/(?P<uuid>[^/]+)/$', views.deploy_online, name="deploy_online"),
    url(r'^poll_state$', views.poll_state,name='poll_state'),
    url(r'^deploy_branch_select/', views.deploy_branch_select, name='deploy_branch_select'),
    url(r'^go_back/(?P<uuid>[^/]+)/$', views.go_back, name="go_back"),
    url(r'^deploy_add_svn/(?P<uuid>[^/]+)/$', views.deploy_add_svn, name="deploy_add_svn"),
    url(r'^deploy_online_svn/(?P<uuid>[^/]+)/$', views.deploy_online_svn, name="deploy_online_svn"),

#"""脚本发布"""
    url(r'^deploy_script/$', sviews.deploy_script, name="deploy_script"),
    url(r'^script_list/$', sviews.list_script, name="script_list"),
    url(r'^script_add/$', sviews.add_script, name="script_add"),
    url(r'^script_edit/(?P<uuid>[^/]+)/$', sviews.edit_script, name="script_edit"),
    url(r'^script_delete/(?P<uuid>[^/]+)/$', sviews.delete_script, name='script_delete'),
    url(r'^script_select/', sviews.script_select, name='script_select'),
    url(r'^script_memo/', sviews.script_memo, name='script_memo'),
    url(r'^script/log', sviews.script_log_list, name='script_log_list'),


#"""gengxin增删查改"""
    url(r'^gengxin_code_list/$', gviews.gengxin_code_list, name="gengxin_code_list"),
    url(r'^gengxin_code_add/$', gviews.gengxin_code_add, name="gengxin_code_add"),
    url(r'^gengxin_code_edit/(?P<uuid>[^/]+)/$', gviews.gengxin_code_edit, name="gengxin_code_edit"),
    url(r'^gengxin_code_delete/(?P<uuid>[^/]+)/$', gviews.gengxin_code_delete, name='gengxin_code_delete'),

    url(r'^gengxin/list/$', gviews.gengxin_deploy_list, name="gengxin_deploy_list"),
    url(r'^genxin/create/(?P<uuid>[^/]+)/$', gviews.gengxin_create_deploy, name='gengxin_create_deploy'),
    url(r'^mytask/', gviews.genxin_my_deploy_task, name='genxin_my_deploy_task'),
    url(r'^mytask_delete/(?P<uuid>[^/]+)/$', gviews.gengxin_my_deploy_task_delete, name='gengxin_my_deploy_task_delete'),



]