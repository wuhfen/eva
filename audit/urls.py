#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from audit import views

urlpatterns = [
#"""运维日志记录"""
    url(r'^record/ops/$', views.record_ops_command, name="record_ops_command"),
    url(r'^record/ops/add/$', views.record_command, name="record_command"),
    url(r'^record/ops/edit/(?P<uuid>[^/]+)/$', views.record_command_edit, name="record_command_edit"),


    url(r'^sql/conf/list/$',views.sql_conf_list,name='sql_conf_list'),
    url(r'^sql/conf/button/$',views.sql_conf_button,name='sql_conf_button'),
    url(r'^sql/conf/add/$',views.sql_conf_add,name='sql_conf_add'),
    url(r'^sql/conf/modify/(?P<uuid>[^/]+)/$',views.sql_conf_modify,name='sql_conf_modify'),
    url(r'^sql/conf/delete/(?P<uuid>[^/]+)/$',views.sql_conf_delete,name='sql_conf_delete'),
    url(r'^sql/conf/status/(?P<uuid>[^/]+)/$',views.sql_conf_check_status,name='sql_conf_check_status'),

    url(r'^sql/statement/add/(?P<uuid>[^/]+)/$',views.sql_apply_add,name='sql_apply_add'),
    url(r'^sql_list/(?P<uuid>[^/]+)/$',views.sql_list,name='sql_list'),
    url(r'^sql/download/(?P<uuid>[^/]+)$',views.sql_file_download,name='sql_download'),
    
    ]