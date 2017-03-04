#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Category(models.Model):  
    name = models.CharField(max_length=20,verbose_name=u'类名')  
  
    def __unicode__(self):  
        return self.name  


class Article(models.Model):
    category = models.ForeignKey(Category,verbose_name=u'分类')
    title = models.CharField(max_length=60,verbose_name=u'标题')
    author = models.CharField(max_length=20,verbose_name=u'作者')
    body = models.TextField(verbose_name=u'文章内容')
    change_date = models.CharField(max_length=20,verbose_name=u'修改时间',default='2017-01-01 12:00:00')
    date = models.DateTimeField(auto_now_add=True,verbose_name=u'时间')

    def __unicode__(self):
        return self.title