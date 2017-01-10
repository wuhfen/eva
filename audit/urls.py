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
    ]