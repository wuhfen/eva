#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from audit import views

urlpatterns = [
#"""运维日志记录"""
    url(r'^record/ops/$', views.record_ops_command, name="record_ops_command"),
    url(r'^record/ops/add/$', views.record_command, name="record_command"),
    url(r'^record/ops/edit/(?P<uuid>[^/]+)/$', views.record_command_edit, name="record_command_edit"),
    # url(r'^line_delete/(?P<uuid>[^/]+)/$', pviews.line_delete, name='line_delete'),
    url(r'^my_audit_list/', views.my_audit_list, name='my_audit_list'),
    url(r'^my_audit_list_delete/(?P<uuid>[^/]+)/$', views.my_audit_delete, name='my_audit_delete'),
    url(r'^my_audit_modify/(?P<uuid>[^/]+)/$', views.my_audit_modify, name='my_audit_modify'),
    url(r'^start/(?P<uuid>[^/]+)/$', views.start_audit, name='start_audit'),
    url(r'^user/list/', views.audit_user_list, name='audit_user_list'),
    url(r'^user/add/', views.audit_user_add, name='audit_user_add'),
    url(r'^user/delete/(?P<uuid>[^/]+)/$', views.audit_user_delete, name='audit_user_delete'),
    url(r'^user/modify/(?P<uuid>[^/]+)/$', views.audit_user_modify, name='audit_user_modify'),


    ]