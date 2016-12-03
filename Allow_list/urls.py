#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from Allow_list import views


urlpatterns = [
    url(r'^error/$',views.error),
    url(r'^welcome/$', views.welcome,name='result-page'),
    url(r'^iptables/$',views.iptables,name='iptables'),
    url(r'^iptables_delete/$',views.iptables_delete,name='delete-ip'),
    url(r'^linechange/$',views.linechange,name='linechange'),
    url(r'^poll_state$', views.poll_state,name='poll_state'),
    
]