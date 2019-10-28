#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.db import models
from accounts.models import CustomUser as Users
from accounts.models import department_Mode as Groups
import uuid

# Create your models here.
class ops_command_log(models.Model):
    #运维审计日志
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    start_time = models.CharField(_(u'开始时间'),max_length=64)
    end_time = models.CharField(_(u'结束时间'),max_length=64)
    command = models.TextField(_(u'内容'))
    user = models.ForeignKey(Users,verbose_name=u'用户')

    class Meta:
        verbose_name = u'运维审计日志'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name

class sql_DangousKey(models.Model):
    dkey = models.CharField(_(u'关键字'),max_length=128,blank=True)
    
    def __unicode__(self):
        return self.dkey

class sql_conf(models.Model):
    """每台数据库的配置,有组的外键,组使用用户组"""
    name = models.CharField(_(u'名称'),max_length=128,blank=True) #显示名称
    host = models.CharField(max_length=15,blank=True)
    user = models.CharField(max_length=28,default='root') #连接主节点所用用户
    port = models.CharField(max_length=6,default=3306) #主节点数据库端口
    password = models.CharField(max_length=100) #主节点用户密码
    status = models.BooleanField(default=False)
    workdir = models.CharField(max_length=64) #文件保存路径/data/sqlfile/host_port
    apply_group = models.ForeignKey(Groups,related_name="apply_sql",blank=True, null=True,on_delete=models.SET_NULL) #申请组
    group = models.ForeignKey(Groups,related_name="audit_sql",blank=True, null=True,on_delete=models.SET_NULL) #审核组
    group_ops = models.ForeignKey(Groups,related_name="ops_audit",blank=True, null=True,on_delete=models.SET_NULL) #特殊审核组,运维人员参与审核

    def __unicode__(self):
        return self.name


class sql_apply(models.Model):
    '''数据库应用:名称,类型(sql文件或语句),文件名,语句,是否审核,是否通过,是否成功,申请人,日志,创建时间,执行时间,备注'''
    sqlconf = models.ForeignKey(sql_conf,null=True,related_name="sqlfile")
    filename = models.TextField(blank=True) #sql文件名
    savename = models.TextField(blank=True) #文件保存名
    md5value = models.CharField(max_length=45,blank=True) #文件的md5值
    md5user = models.CharField(max_length=45,blank=True) #用户输入的md5值
    dangerous = models.BooleanField(default=False)  #是否触发关键字
    keyword = models.TextField(null=True,blank=True)  #触发关键字语句
    review = models.BooleanField(default=False)  #是否已审核
    passed = models.BooleanField(default=False) #审核是否通过
    islog = models.BooleanField(default=False) #是否执行完毕
    log = models.TextField(null=True,blank=True) #本条执行结果返回
    memo = models.TextField(null=True,blank=True) #备注
    user = models.ForeignKey(Users,null=True,verbose_name=u'申请人')
    etime = models.DateTimeField(auto_now=True)
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = u'数据库执行申请'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.md5user