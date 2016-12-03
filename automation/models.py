#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models
from assets.models import Server as hosts
from accounts.models import CustomUser as Users
from business.models import Business 
# Create your models here.

import uuid


class Tools(models.Model):
    #"""git或svn的详细信息"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    TOOL_TYPE = [(i, i) for i in (u"GIT",u"Subversion")]
    name =models.CharField(_(u'名称'),max_length=32, choices=TOOL_TYPE)
    title = models.CharField(_(u'标题'), max_length=64, unique=True)
    address = models.CharField(_(u'地址'), max_length=128, blank=True)
    user = models.CharField(_(u'用户'), max_length=64, blank=True)
    passwd = models.CharField(_(u'密码'), max_length=64, blank=True)

    class Meta:
        verbose_name = u'版本管理工具'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.title


class Confile(models.Model):
    #"""关联业务的版本发布需要的一些信息"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(_(u'发布标题'), max_length=64, unique=True)
    ENVIRONMENT_SELECT = (
    ("production",u"线上环境"),
    ("test",u"测试环境"),
    )
    environment = models.CharField(max_length=64, choices=ENVIRONMENT_SELECT,verbose_name=u'部署环境')
    tool = models.ForeignKey(Tools,on_delete=models.SET_NULL, blank=True,null=True,verbose_name=u'代码仓库')
    business = models.ForeignKey(Business,verbose_name=u'关联业务', blank=True,null=True)
    localhost_dir = models.CharField(_(u'code检出仓库'), max_length=128, blank=True)
    exclude = models.TextField(_(u'排除文件'),blank=True)
    webroot_user = models.CharField(_(u'web用户'), max_length=32,default='www')
    webroot = models.CharField(_(u'web目录'), max_length=128)
    relaese_dir = models.CharField(_(u'发布版本库'), max_length=64)
    max_number = models.IntegerField(_(u'保留版本数'), blank=True,default=10)
    server_list = models.TextField(_(u'服务器列表'), blank=True)
    pre_deploy = models.TextField(_(u'部署前动作'), blank=True)
    post_deploy = models.TextField(_(u'部署后动作'), blank=True)
    pre_release = models.TextField(_(u'版本拉取前动作'), blank=True)
    post_release = models.TextField(_(u'版本拉取后动作'), blank=True)
    status = models.BooleanField(default=True,verbose_name=u'是否启用')


    class Meta:
        verbose_name = u'版本发布属性'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name



class deploy(models.Model):
    #"""申请发布表单，用户只需要填写名称，分支与版本"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    ctime = models.DateTimeField(verbose_name=u'创建时间',blank=True, auto_now=True)
    name = models.CharField(_(u'发布名称'),max_length=64)
    branches = models.CharField(_(u'分支'),max_length=64,blank=True)
    release = models.CharField(_(u'commit_id'),max_length=64,blank=True)
    executive_user = models.ForeignKey(Users,verbose_name=u'用户')
    confile = models.ForeignKey('Confile',verbose_name=u'发布项目配置')
    CONFILE_CHECK = [(i, i) for i in (u'已通过',u'未通过')]
    check_conf = models.CharField(_(u'审核状态'),max_length=32,choices=CONFILE_CHECK,blank=True)
    STATUS_CHECK = [(i, i) for i in (u'已发布',u'未发布',u'已回滚')]
    status = models.CharField(_(u'状态'),max_length=32,choices=STATUS_CHECK,default=u'未发布',blank=True)
    tag = models.CharField(_(u'标签'),max_length=64,blank=True)
    memo = models.TextField(_(u'发布原因'))
    execution_time = models.IntegerField(_(u'发布时间'),default=0)
    exist = models.BooleanField(default='False')


    class Meta:
        verbose_name = u'发布申请单'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name











