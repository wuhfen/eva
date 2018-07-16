#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from accounts.models import CustomUser as User
from business.models import Business
from gitfabu.models import git_deploy

# Create your models here.
class Iptables(models.Model):
    ## 执行操作的serverip
    host_ip = models.GenericIPAddressField(max_length=15, default='0.0.0.0')
    ## 备注信息
    i_comment = models.CharField(max_length=50, blank=True)
    ## 执行的表 -t 指定表，默认filter
    i_table = models.CharField(max_length=50, blank=True, default='filter')
    ## 动作，默认是插入，还有追加-A，替换-P, 删除-D
    i_method = models.CharField(max_length=10, default='-I')
    ## 链,FORWARD，INPUT，OUTPUT
    i_chain = models.CharField(max_length=20, default='INPUT')
    ## 插入链中的位置
    i_position = models.CommaSeparatedIntegerField(max_length=30, blank=True,default=3)
    ## 源ip
    i_source_ip = models.GenericIPAddressField(max_length=15, null=True, default='0.0.0.0')
    ## 目标ip
    i_destination_ip = models.GenericIPAddressField(max_length=15, null=True, default='0.0.0.0')
    ## 协议，tcp，udp，icmp
    i_protocol = models.CharField(max_length=8,default='tcp')
    ## 端口指定 --dport --sport --dports --sports
    i_port_method = models.CharField(max_length=30, blank=True,default='--dports')
    ## 端口 80，443，22，25，3306
    i_ports = models.CommaSeparatedIntegerField(max_length=30, blank=True ,default='80,443')
    ## --state NEW
    i_states = models.CharField(max_length=50, blank=True, default='NEW,ESTABLISHED')
    ## 规则接受还是拒绝DORP
    i_target = models.CharField(max_length=8,default='ACCEPT')
    ## 时间
    i_date_time = models.DateTimeField(auto_now_add=True)
    ## 用户
    i_user = models.ForeignKey(User,on_delete=models.CASCADE)
    ## 标记，主要是标记ansible的hosts中的哪一个组执行了这个规则
    i_remark = models.CharField(max_length=50, null=True, blank=True)
    ## 标签
    i_tag = models.CharField(max_length=50, blank=True,default='新平台')
    i_platform = models.CharField(max_length=50,blank=True,null=True)


    def __unicode__(self):
        return self.i_comment
    class Meta:
        ordering = ['i_comment']
        verbose_name = u"白名单管理"
        verbose_name_plural = verbose_name

class oldsite_line(models.Model):
    """docstring for oldsite_line"""
    host_ip = models.TextField(u'后台反代站',blank=True, null=True)
    agent = models.CharField(max_length=50, blank=True, null=True) #客户网站名称
    agent_name = models.CharField(max_length=50,blank=True, null=True) #客户网站拼写
    line = models.CharField(max_length=50,blank=True, null=True)
    number = models.PositiveIntegerField(default='0')
    status = models.BooleanField(default=False)
    comment = models.CharField(max_length=200,blank=True, null=True)
    date_time = models.CharField(max_length=38, blank=True,null=True)

    def __unicode__(self):
        return self.agent
    class Meta:
        verbose_name = u"后台线路管理"
        verbose_name_plural = verbose_name


class white_conf(models.Model):
    NAME = (
    ('DT-GFC',u'鼎泰官方彩白名单'),
    ('MN-GFC',u'蛮牛官方彩白名单'),
    ('MN-JDC',u'蛮牛经典彩白名单'),
    ('KG-JDC',u'KG经典彩白名单'),
    ('MN-Backend',u'蛮牛后台白名单'),
    ('MONEY-Backend',u'现金网后台白名单'),
    ('MONEY-Black',u'现金网后台黑名单'),
    ('MN-Black',u'蛮牛后台黑名单'),
    )
    name = models.CharField(_(u'白名单配置'),max_length=25,choices=NAME,unique=True)
    servers = models.TextField(_(u'服务器地址'))
    file_path = models.CharField(_(u'文件绝对路径'),max_length=100)
    is_reload = models.BooleanField(_(u'是否重启'),default=False)
    exception_ip = models.TextField(_(u'例外IP'),null=True,blank=True) #例外IP,记录后此IP可以随便添加几次,否则只能5次


class white_list(models.Model):
    u"""基于NGINX配置文件的白名单实现，allow和deny为key，ip为value,
    deny单个ip为先, allow单个ip为中，deny放最后，allow为默认，不需要设置
    """
    KEY = (
    ('allow',u'允许'),
    ('deny',u'拒绝'),
    )
    host_key = models.CharField(_(u'白名单key'),max_length=10,choices=KEY)
    host_ip = models.CharField(_(u'白名单value'),max_length=15)
    git_deploy = models.ForeignKey(git_deploy,null=True,blank=True,related_name='white')
    white_conf = models.ForeignKey(white_conf)
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    ctime = models.DateTimeField(auto_now_add=True)