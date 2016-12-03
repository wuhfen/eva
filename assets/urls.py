#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from assets import views
from assets.project_asset import views as pviews
from assets.idc_asset import views as idcviews


urlpatterns = [
#"""产品线增删查改"""
    url(r'^line_add/$', pviews.line_add, name="line_add"),
    url(r'^line_list/$', pviews.line_list, name="line_list"),
    url(r'^line_edit/(?P<uuid>[^/]+)/$', pviews.line_edit, name="line_edit"),
    url(r'^line_delete/(?P<uuid>[^/]+)/$', pviews.line_delete, name='line_delete'),

#"""项目增删查改"""
    url(r'^project_add/$',pviews.project_add,name="project_add"),
    url(r'^project_list/', pviews.project_list, name='project_list'),
    url(r'^project_edit/(?P<uuid>[^/]+)/$', pviews.project_edit, name='project_edit'),
    url(r'^project_delete/(?P<uuid>[^/]+)/$', pviews.project_delete, name='project_delete'),

#"""添加机房信息"""
   url(r'^idc_add/$', idcviews.idc_add,name="idc_add"),
   url(r'^idc_list/$', idcviews.idc_list,name="idc_list"),
   url(r'^idc_edit/(?P<uuid>[^/]+)/$', idcviews.idc_edit,name="idc_edit"),
   url(r'^idc_delete/(?P<uuid>[^/]+)/$', idcviews.idc_delete,name="idc_delete"),
   url(r'^idc_details/(?P<uuid>[^/]+)/$', idcviews.idc_details,name="idc_details"),

#"""机房区域信息"""
   url(r'^moudle_add/$', idcviews.moudle_add,name="moudle_add"),
   url(r'^moudle_list/$', idcviews.moudle_list,name="moudle_list"),
   url(r'^moudle_edit/(?P<uuid>[^/]+)/$', idcviews.moudle_edit,name="moudle_edit"),
   url(r'^moudle_delete/(?P<uuid>[^/]+)/$', idcviews.moudle_delete,name="moudle_delete"),

#"""机房机柜信息"""
   url(r'^cabinet_add/$', idcviews.cabinet_add,name="cabinet_add"),
   url(r'^cabinet_list/$', idcviews.cabinet_list,name="cabinet_list"),
   url(r'^cabinet_edit/(?P<uuid>[^/]+)/$', idcviews.cabinet_edit,name="cabinet_edit"),
   url(r'^cabinet_delete/(?P<uuid>[^/]+)/$', idcviews.cabinet_delete,name="cabinet_delete"),

#"""系统服务信息"""
   url(r'^service_add/$', pviews.service_add,name="service_add"),
   url(r'^service_list/$', pviews.service_list,name="service_list"),
   url(r'^service_edit/(?P<uuid>[^/]+)/$', pviews.service_edit,name="service_edit"),
   url(r'^service_delete/(?P<uuid>[^/]+)/$', pviews.service_delete,name="service_delete"),

#"""添加服务器"""
   url(r'^server_add/$', views.server_add,name="server_add"),
   url(r'^server_list/$', views.server_list,name="server_list"),
   url(r'^server_detail/(?P<uuid>[^/]+)/$', views.server_detail,name="server_detail"),
   url(r'^server_edit/(?P<uuid>[^/]+)/$', views.server_edit,name="server_edit"),


#"""添加虚拟机"""
   url(r'^virtual_add/$', views.virtual_add,name="virtual_add"),
   url(r'^virtual_detail/(?P<uuid>[^/]+)/$', views.virtual_detail,name="virtual_detail"),
   url(r'^virtual_edit/(?P<uuid>[^/]+)/$', views.virtual_edit,name="virtual_edit"),

#"""网卡操作"""
   url(r'^nic_add/(?P<uuid>[^/]+)/$', views.nic_add,name="nic_add"),
   url(r'^nic_delete/(?P<uuid>[^/]+)/$', views.nic_delete,name="nic_delete"),
   url(r'^nic_edit/(?P<uuid>[^/]+)/$', views.nic_edit,name="nic_edit"),


#"""内存条操作"""
   url(r'^ram_add/(?P<uuid>[^/]+)/$', views.ram_add,name="ram_add"),
   url(r'^ram_delete/(?P<uuid>[^/]+)/$', views.ram_delete,name="ram_delete"),
   url(r'^ram_edit/(?P<uuid>[^/]+)/$', views.ram_edit,name="ram_edit"),


#"""硬盘操作"""
   url(r'^disk_add/(?P<uuid>[^/]+)/$', views.disk_add,name="disk_add"),
   url(r'^disk_delete/(?P<uuid>[^/]+)/$', views.disk_delete,name="disk_delete"),
   url(r'^disk_edit/(?P<uuid>[^/]+)/$', views.disk_edit,name="disk_edit"),



#"""Raid卡操作"""
   url(r'^raid_add/(?P<uuid>[^/]+)/$', views.raid_add,name="raid_add"),
   url(r'^raid_delete/(?P<uuid>[^/]+)/$', views.raid_delete,name="raid_delete"),
   url(r'^raid_edit/(?P<uuid>[^/]+)/$', views.raid_edit,name="raid_edit"),




]