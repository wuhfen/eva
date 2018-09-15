#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from business import views
# from business import platfapi
from business.dnsmanage import views as dnsviews

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


##IP管理
    url(r'^domain_ip_list/$', views.domain_ip_list, name="domain_ip_list"),
    url(r'^domain_ip_add/$', views.domain_ip_add, name="domain_ip_add"),
    url(r'^domain_ip_edit/(?P<uuid>[^/]+)/$', views.domain_ip_edit, name="domain_ip_edit"),
    url(r'^domain_ip_delete/(?P<uuid>[^/]+)/$', views.domain_ip_delete, name="domain_ip_delete"),

##域名
    url(r'^domain_list/(?P<siteid>[^/]+)/$', views.domain_list_select, name="domain_list_select"),
    url(r'^domain/add_select/(?P<siteid>[^/]+)/$', views.domain_add_select, name="domain_add_select"),
    url(r'^domain_edit/(?P<uuid>[^/]+)/$', views.domain_edit, name="domain_edit"),
    url(r'^domain_delete/(?P<uuid>[^/]+)/$', views.domain_delete, name="domain_delete"),
    url(r'^domain_detail/(?P<uuid>[^/]+)/$', views.domain_detail, name="domain_detail"),
    url(r'^domain_add_batch/$', views.domain_add_batch, name="domain_add_batch"),
    url(r'^all/list/$', views.domain_manage_business_list, name="domain_manage_business_list"),


##更新域名至服务器
    # url(r'^domain_rsync/(?P<uuid>[^/]+)/$', views.business_domain_rsync, name="domain_rsync"),
    # url(r'^domain_rsync_to_server/$', views.domain_rsync_to_server, name="domain_rsync_to_server"),

    url(r'^upload/file/$', views.domain_upload, name="domain_upload"),



##域名监控
    url(r'^domain/monitor/(?P<uuid>[^/]+)/$',views.domain_monitor,name="domain_monitor"),
    url(r'^domain/change_monitor_status/',views.change_domain_monitor_status,name="change_domain_monitor_status"),
    url(r'^domain/get_status/',views.get_domain_status,name="get_domain_status"),
    url(r'^domain/get_code/',views.get_domain_code,name="get_domain_code"),
    url(r'^domain/monitor_restart/',views.restart_all_monitor,name="restart_all_monitor"),


##DNS管理
    url(r'^domain/manage/user/list/$', dnsviews.dnsuser_list, name="dnsuser_list"),
    url(r'^domain/manage/user/add/$',dnsviews.dnsuser_add,name="dnsuser_add"),
    url(r'^domain/manage/user/delete/(?P<id>[^/]+)/$',dnsviews.dnsuser_delete,name="dnsuser_delete"),
    url(r'^domain/manage/user/edit/(?P<id>[^/]+)/$',dnsviews.dnsuser_edit,name="dnsuser_edit"),
    url(r'^domain/manage/user/domain/pull/(?P<id>[^/]+)/$',dnsviews.dnsuser_get_domainname,name="dnsuser_get_domainname"),


    url(r'^domain/manage/domain/list/1$', dnsviews.dnsname_list, name="dnsname_list"),
    url(r'^domain/manage/domain/add/$', dnsviews.dnsname_add_one, name="dnsname_add_one"),
    url(r'^domain/manage/domain/remark/$', dnsviews.dnsname_domain_remark, name="dnsname_domain_remark"), #更新域名备注

    url(r'^domain/manage/domain/status/$', dnsviews.dnsname_status_change, name="dnsname_status_change"),

    url(r'^domain/manage/domain/delete/(?P<id>[^/]+)/$', dnsviews.dnsname_delete, name="dnsname_delete"),
    url(r'^domain/manage/domain/detail/(?P<id>[^/]+)/$', dnsviews.dnsname_detail, name="dnsname_detail"),
    url(r'^domain/manage/domain/records/(?P<id>[^/]+)/$', dnsviews.dnsname_get_records, name="dnsname_get_records"),

##记录管理
    url(r'^domain/manage/records/add/(?P<id>[^/]+)/$',dnsviews.dnsname_add_records,name="dnsname_add_records"),
    url(r'^domain/manage/record/add/(?P<id>[^/]+)/$',dnsviews.dnsname_add_one_record,name="dnsname_add_one_record"),
    url(r'^domain/manage/record/modify/(?P<uuid>[^/]+)/$',dnsviews.dnsname_record_modify,name="dnsname_record_modify"),
    url(r'^domain/manage/record/delete/(?P<uuid>[^/]+)/$',dnsviews.dnsname_record_delete,name="dnsname_record_delete"),
    url(r'^domain/manage/record/standby/$', dnsviews.dnsname_record_standby, name="dnsname_record_standby"),
    url(r'^domain/manage/record/switcher/$', dnsviews.dnsname_record_switcher, name="dnsname_record_switcher"),
    url(r'^domain/manage/record/list/$', dnsviews.dnsname_record_list, name="dnsname_record_list"),
    url(r'^domain/manage/record/status/$', dnsviews.dnsname_record_status, name="dnsname_record_status"), #改变记录状态


##一键转移域名
    url(r'^domain/manage/domain/transfer/(?P<uuid>[^/]+)/$', dnsviews.dnsname_transfer, name="dnsname_transfer"),

##加速服务器管理
    url(r'acceleration/list/',views.acceleration_node_list,name="jiasu_list"),
    url(r'acceleration/add/',views.acceleration_node_add,name="jiasu_add"),
    url(r'acceleration/delete/(?P<uuid>[^/]+)/$',views.acceleration_node_delete,name="jiasu_delete"),
    url(r'acceleration/modify/(?P<uuid>[^/]+)/$',views.acceleration_node_modify,name="jiasu_modify"),




]