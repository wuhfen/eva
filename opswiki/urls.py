#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from opswiki import views
from opswiki.forms import ArticleForm
from django.views.generic import FormView

urlpatterns = [
##"""wiki"""
    url(r'^article/list/$', views.list_article, name="list_article"),
    url(r'^article/show/(?P<id>[^/]+)/$', views.show_article, name="show_article"),
    url(r'^article/edit/(?P<id>[^/]+)/$', views.edit_article, name="edit_article"),
    url(r'^article/write/$', views.write_article, name="write_article"),


    # url(r'^tools_list/$', views.tools_list, name="tools_list"),
    # url(r'^tools_delete/(?P<uuid>[^/]+)/$', views.tools_delete, name='tools_delete'),
]