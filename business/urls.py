#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from business import views
from business import platfapi

urlpatterns = [
##业务
    url(r'^business_add/$', views.business_add, name="business_add"),
    url(r'^business_list/$', views.business_list, name="business_list"),
    url(r'^business_delete/(?P<uuid>[^/]+)/$', views.business_delete, name="business_delete"),
    url(r'^business_edit/(?P<uuid>[^/]+)/$', views.business_edit, name="business_edit"),
    url(r'^business_detail/(?P<uuid>[^/]+)/$', views.business_detail, name="business_detail"),
##查看配置文件
    url(r'^business/conf/show',views.business_conf_show,name="business_conf_show"),
    url(r'^business/conf/create',views.deploy_nginx_tmp_file,name="deploy_nginx_tmp_file"),


##BUG
    url(r'^bugs_list/$', views.bugs_list, name="bugs_list"),

##平台
    url(r'^platform_list/$', views.platform_list, name="platform_list"),
    url(r'^platform_detail/(?P<uuid>[^/]+)/$', views.platform_detail, name="platform_detail"),
    url(r'^platform_edit/(?P<uuid>[^/]+)/$', views.platform_edit, name="platform_edit"),
    url(r'^platform_add/$', views.platform_add, name="platform_add"),
    # url(r'^platform_delete/$', views.platform_delete, name="platform_delete"),


##IP管理
    url(r'^domain_ip_list/$', views.domain_ip_list, name="domain_ip_list"),
    url(r'^domain_ip_add/$', views.domain_ip_add, name="domain_ip_add"),
    url(r'^domain_ip_edit/(?P<uuid>[^/]+)/$', views.domain_ip_edit, name="domain_ip_edit"),
    url(r'^domain_ip_delete/(?P<uuid>[^/]+)/$', views.domain_ip_delete, name="domain_ip_delete"),



##域名
    url(r'^domain_list/$', views.domain_list, name="domain_list"),
    url(r'^domain_add/$', views.domain_add, name="domain_add"),
    url(r'^domain_edit/(?P<uuid>[^/]+)/$', views.domain_edit, name="domain_edit"),
    url(r'^domain_delete/(?P<uuid>[^/]+)/$', views.domain_delete, name="domain_delete"),
    url(r'^domain_detail/(?P<uuid>[^/]+)/$', views.domain_detail, name="domain_detail"),
    url(r'^domain_add_batch/$', views.domain_add_batch, name="domain_add_batch"),


##更新域名至服务器
    url(r'^domain_rsync/(?P<uuid>[^/]+)/$', views.business_domain_rsync, name="domain_rsync"),
    url(r'^domain_rsync_to_server/$', views.domain_rsync_to_server, name="domain_rsync_to_server"),



##域名监控
    url(r'^domain/monitor/(?P<uuid>[^/]+)/$',views.domain_monitor,name="domain_monitor"),
    url(r'^domain/change_monitor_status/',views.change_domain_monitor_status,name="change_domain_monitor_status"),
    url(r'^domain/get_status/',views.get_domain_status,name="get_domain_status"),
    url(r'^domain/get_code/',views.get_domain_code,name="get_domain_code"),
    url(r'^domain/monitor_restart/',views.restart_all_monitor,name="restart_all_monitor"),


##白名单
##API
    url(r'^platform_api/$', platfapi.get_platform_data),


]