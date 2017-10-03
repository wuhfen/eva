#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from Allow_list import views


urlpatterns = [
    url(r'^error/$',views.error),
    url(r'^welcome/$', views.welcome,name='result-page'),
    url(r'^iptables/$',views.iptables,name='iptables'),
    url(r'^iptables_delete/(?P<id>[^/]+)/$',views.iptables_delete,name='delete-ip'),
    url(r'^iptables/search/(?P<comment>[^/]+)/$',views.iptables_search,name='iptables_search'),
    url(r'^linechange/$',views.linechange,name='linechange'),
    url(r'^poll_state$', views.poll_state,name='poll_state'),
    url(r'^linechange/pulldata/(?P<choice>[^/]+)/$', views.pull_data, name="allow_pull_data"),
    url(r'^linechange/pushdata/(?P<choice>[^/]+)/$', views.push_data, name="allow_push_data"),
    #"""域名解析"""

    url(r'^backend/status/',views.backend_status,name='backend_status'),
    url(r'^backend/change/(?P<id>[^/]+)/$',views.change_backend,name='change_backend'),
    url(r'^domain/list/$',views.kefu_domain_list,name='kefu_domain_list'),

    
]