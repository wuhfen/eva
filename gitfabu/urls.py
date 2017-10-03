#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from gitfabu import views

urlpatterns = [
    url(r'^conf/list/$', views.conf_list, name="conf_list"),
    url(r'^conf/add/(?P<env>[^/]+)/$', views.conf_add, name="conf_add"),
    url(r'^mytask/$', views.my_request_task_list, name="my_request_task_list"),
    url(r'^otherstask/$', views.others_request_task_list, name="others_request_task_list"),
    url(r'^cancel/task/(?P<uuid>[^/]+)/$', views.cancel_my_task, name="cancel_my_task"),
    url(r'^task/details/(?P<uuid>[^/]+)/$', views.my_task_details, name="my_task_details"),
    url(r'^task/audit/(?P<uuid>[^/]+)/$', views.audit_my_task, name="audit_my_task"),
    url(r'^web/update/(?P<uuid>[^/]+)/$', views.web_update_code, name="web_update_code"),
    url(r'^public/update/(?P<env>[^/]+)/$', views.public_update_code, name="public_update_code"),
    url(r'^git_batch_change/(?P<uuid>[^/]+)/$', views.batch_change, name="batch_change"),
    url(r'^pubilc_branch_change/$', views.public_branch_change, name="public_branch_change"),

]