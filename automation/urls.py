#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from automation import views
from automation import script_deploy as sviews

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






]