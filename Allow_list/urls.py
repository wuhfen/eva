#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from Allow_list import views,ngx_acl


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
    url(r'^white/batch/add/(?P<uuid>[^/]+)/$',views.white_batch_add,name='white_batch_add'),
    url(r'^white/vip/(?P<uuid>[^/]+)/$',views.white_vip,name='white_vip'), #特权vip,可添加超过5次限制
    url(r'^white/delete/(?P<uuid>[^/]+)/$',views.white_delete,name='white_delete'),
    url(r'^white/search/$',views.white_list_search,name='white_list_search'),
    url(r'^white/batch/delete/$',views.batch_delete_vpn,name='batch_delete_vpn'),
    #黑名单
    url(r'^black/list/$',views.black_list_fun,name='black_list'),
    url(r'^black/add/$',views.black_add,name='black_add'),

    #过期提醒
    url(r'^reminder/list/$',views.reminder_list,name='reminder_list'),
    url(r'^reminder/add/$',views.reminder_add,name='reminder_add'),



    #访问控制系统top
    url(r'^display/$',ngx_acl.nginx_acl_display,name="nginx_acl_display"),
    url(r'^preadd/display/$',ngx_acl.pre_add_display,name="pre_add_display"),
    url(r'^preadd/detail/',ngx_acl.pre_add_detail,name="predetail"),
    url(r'^topproject/display/$',ngx_acl.top_pro_display,name="top_pro_display"),
    url(r'^exception/display/$',ngx_acl.nginx_acl_exception,name="acl_exception_display"),
    url(r'^subproject/display/',ngx_acl.sub_pro_display,name="sub_pro_display"),
    url(r'^tapi/$',ngx_acl.top_pro_api,name="tapi"),
    url(r'^sapi/$',ngx_acl.sub_pro_api,name="sapi"),
    url(r'^napi/$',ngx_acl.nginx_acl_api,name="napi"),
    url(r'^papi/$',ngx_acl.pre_add_api,name="papi"),
    url(r'^tpadd/$',ngx_acl.top_pro_add,name="tpadd"),
    url(r'^spadd/(?P<tid>[^/]+)/$',ngx_acl.sub_pro_add,name="spadd"),
    url(r'^preadd/$',ngx_acl.pre_add,name="preadd"),
    url(r'^acladd/$',ngx_acl.nginx_acl_add,name="acladd"),
    url(r'^tpservers/',ngx_acl.top_servers_edit,name="tpservers"),
    url(r'^spservers/',ngx_acl.sub_servers_edit,name="spservers"),
    url(r'^tpexception/$',ngx_acl.top_exception_edit,name="tpexception"),

]