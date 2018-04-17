#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from Allow_list import views


urlpatterns = [
    url(r'^error/$',views.error),
    url(r'^welcome/$', views.welcome,name='result-page'),
    url(r'^iptables/$',views.iptables,name='iptables'),
    url(r'^iptables/list/$',views.iptables_list,name='iptables_list'),
    url(r'^iptables_delete/(?P<id>[^/]+)/$',views.iptables_delete,name='delete-ip'),
    url(r'^iptables/search/$',views.iptables_search,name='iptables_search'),
    url(r'^linechange/$',views.linechange,name='linechange'),
    url(r'^poll_state$', views.poll_state,name='poll_state'),
    url(r'^linechange/pulldata/(?P<choice>[^/]+)/$', views.pull_data, name="allow_pull_data"),
    url(r'^linechange/pushdata/(?P<choice>[^/]+)/$', views.push_data, name="allow_push_data"),
    #"""域名解析"""

    url(r'^backend/status/',views.backend_status,name='backend_status'),
    url(r'^backend/change/(?P<id>[^/]+)/$',views.change_backend,name='change_backend'),

    #"""白名单服务器配置"""
    url(r'^white/conf/list/$',views.white_conf_list,name='white_conf_list'),
    url(r'^white/conf/modify/(?P<uuid>[^/]+)/$',views.white_conf_modify,name='white_conf_modify'),
    #白名单
    url(r'^white/list/(?P<which>[^/]+)/$',views.white_list_fun,name='white_list'),
    url(r'^white/add/(?P<uuid>[^/]+)/$',views.white_add,name='white_add'),
    url(r'^white/delete/(?P<uuid>[^/]+)/$',views.white_delete,name='white_delete'),
    url(r'^white/search/$',views.white_list_search,name='white_list_search'),
    #黑名单
    url(r'^black/list/$',views.black_list_fun,name='black_list'),
    url(r'^black/add/$',views.black_add,name='black_add'),




]