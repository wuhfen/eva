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



SQL_TYPE = [(i, i) for i in (u'文件',u'语句')]

class sql_conf(models.Model):
    """每台数据库的配置,有组的外键,组使用用户组"""
    name = models.CharField(_(u'名称'),max_length=128,blank=True) #显示名称
    pub_vip = models.CharField(_(u'公网VIP'),max_length=15,blank=True) #公网vip
    local_vip = models.CharField(_(u'内网VIP'),max_length=15,blank=True) #内网vip
    vip_port = models.CharField(_(u'VIP调用端口'),max_length=6,default=3306) #给用户的调用端口
    cluster = models.BooleanField(_(u'是否为集群'),default=False) #是否为集群
    master_node = models.GenericIPAddressField(_(u'主节点')) #集群主节点,sql会在此节点执行
    slave_node = models.TextField(_(u'从节点'),blank=True,null=True)  #从节点
    user = models.CharField(max_length=28,default='root') #连接主节点所用用户
    port = models.CharField(max_length=6,default=3306) #主节点数据库端口
    password = models.CharField(max_length=100) #主节点用户密码
    group = models.ForeignKey(Groups,blank=True, null=True,on_delete=models.SET_NULL) #所属组审核组

    def __unicode__(self):
        return self.name


class sql_apply(models.Model):
    '''数据库应用:名称,类型(sql文件或语句),文件名,语句,是否审核,是否通过,是否成功,申请人,日志,创建时间,执行时间,备注'''
    name = models.ForeignKey(sql_conf)
    database = models.CharField(max_length=28,blank=True)
    sql_type = models.CharField(max_length=10,blank=True,choices=SQL_TYPE)  #文件或语句
    md5v = models.CharField(max_length=45,blank=True) #文件的md5值
    statement = models.TextField(blank=True)  #上传文件名
    file_path = models.TextField(blank=True) #文件存放路径
    file_name = models.TextField(blank=True) #文件存储名
    status = models.CharField(max_length=20,blank=True)  #完成,等待,取消
    isaudit = models.BooleanField(default=False) #审核是否通过
    islog = models.BooleanField(default=False) #是否执行
    log = models.TextField(null=True,blank=True) #本条执行结果返回
    memo = models.TextField(null=True,blank=True) #备注
    etime = models.DateTimeField(auto_now=True)
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = u'数据库执行申请'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name