#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from gitfabu import views

urlpatterns = [
    url(r'^conf/list/$', views.conf_list, name="conf_list"),
    url(r'^conf/admin/$', views.conf_admin, name="conf_admin"),
    url(r'^conf/server/(?P<id>[^/]+)/$', views.deploy_servers, name="deploy_servers"),
    url(r'^conf/gitrepo/(?P<id>[^/]+)/$', views.deploy_gitrepo, name="deploy_gitrepo"),
    url(r'^conf/edit/(?P<id>[^/]+)/$', views.deploy_edit, name="deploy_edit"),
    url(r'^conf/del/(?P<id>[^/]+)/$', views.deploy_del, name="deploy_del"),
    url(r'^conf/version/(?P<id>[^/]+)/$', views.deploy_version, name="deploy_version"),
    url(r'^conf/version/update$', views.deploy_version_updata_api, name="deploy_version_updata_api"),



    url(r'^conf/add/(?P<env>[^/]+)/$', views.conf_add, name="conf_add"),
    url(r'^conf/add_alone/$', views.conf_add_alone_project, name="conf_add_alone_project"),
    url(r'^conf/add_java/$', views.conf_add_java_project, name="conf_add_java_project"),
    url(r'^mytask/$', views.my_request_task_list, name="my_request_task_list"),
    url(r'^mytask/filter/$', views.my_request_task_filter, name="my_request_task_filter"),
    url(r'^observer/$', views.task_observer, name="task_observer"),

    url(r'^otherstask/$', views.others_request_task_list, name="others_request_task_list"),
    url(r'^otherstask/filter/$', views.others_request_task_filter, name="others_request_task_filter"),
    url(r'^cancel/task/(?P<uuid>[^/]+)/$', views.cancel_my_task, name="cancel_my_task"),
    url(r'^task/details/(?P<uuid>[^/]+)/$', views.my_task_details, name="my_task_details"),
    url(r'^task/audit/(?P<uuid>[^/]+)/$', views.audit_my_task, name="audit_my_task"),
    url(r'^task/onekey/(?P<uuid>[^/]+)/$', views.one_key_task, name="one_key_task"), #一键审核
    url(r'^web/update/(?P<uuid>[^/]+)/$', views.web_update_code, name="web_update_code"),
    url(r'^public/update/(?P<env>[^/]+)/$', views.public_update_code, name="public_update_code"),
    url(r'^git_batch_change/(?P<uuid>[^/]+)/$', views.batch_change, name="batch_change"),
    url(r'^pubilc_branch_change/$', views.public_branch_change, name="public_branch_change"),
    url(r'^version/list/(?P<uuid>[^/]+)/$', views.version_list, name="version_list"),

    url(r'^manniu/list/$', views.manniu_list, name="manniu_list"),
    url(r'^vue_manniu/list/$', views.vue_manniu_list, name="vue_manniu_list"),
    url(r'^audit/list/$', views.audit_list, name="audit_list"),
    url(r'^audit/manage/(?P<uuid>[^/]+)/$', views.audit_manage, name="audit_manage"),

    #confirm_mytask复核
    url(r'^task/confirm/(?P<uuid>[^/]+)/$', views.confirm_mytask, name="confirm_mytask"),
    url(r'^conf/domains/$', views.deploy_domains, name="deploy_domains"),

    url(r'^vue/wap/(?P<env>[^/]+)/$', views.vue_wap_batch_update, name="vue_wap_batch_update"),
    url(r'^vue/pc/(?P<env>[^/]+)/$', views.vue_pc_batch_update, name="vue_pc_batch_update"),
    url(r'^money/web/(?P<env>[^/]+)/$', views.money_web_batch_update, name="money_web_batch_update"),
    url(r'^money/pc/(?P<env>[^/]+)/$', views.money_pc_batch_update, name="money_pc_batch_update"),
]