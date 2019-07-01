#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

from django.db import models
from cmdb.cmdbBaseModel import BaseModel
from django.utils.translation import ugettext as _
from accounts.models import CustomUser as User
from business.models import Business
from gitfabu.models import git_deploy

# Create your models here.
class Iptables(models.Model):
    host_ip = models.GenericIPAddressField(max_length=15, default='0.0.0.0') ## 执行操作的serverip
    i_comment = models.CharField(max_length=50, blank=True) ## 备注信息
    i_table = models.CharField(max_length=50, blank=True, default='filter') ## 执行的表 -t 指定表，默认filter
    i_method = models.CharField(max_length=10, default='-I') ## 动作，默认是插入，还有追加-A，替换-P, 删除-D
    i_chain = models.CharField(max_length=20, default='INPUT') ## 链,FORWARD，INPUT，OUTPUT
    i_position = models.CharField(max_length=30, blank=True,default=3) ## 插入链中的位置
    i_source_ip = models.GenericIPAddressField(max_length=15, null=True, default='0.0.0.0') ## 源ip
    i_destination_ip = models.GenericIPAddressField(max_length=15, null=True, default='0.0.0.0') ## 目标ip
    i_protocol = models.CharField(max_length=8,default='tcp') ## 协议，tcp，udp，icmp
    i_port_method = models.CharField(max_length=30, blank=True,default='--dports') ## 端口指定 --dport --sport --dports --sports
    i_ports = models.CharField(max_length=30, blank=True ,default='80,443') ## 端口 80，443，22，25，3306
    i_states = models.CharField(max_length=50, blank=True, default='NEW,ESTABLISHED') ## --state NEW
    i_target = models.CharField(max_length=8,default='ACCEPT') ## 规则接受还是拒绝DORP
    i_date_time = models.DateTimeField(auto_now_add=True)## 时间
    i_user = models.ForeignKey(User,on_delete=models.CASCADE)## 用户
    i_remark = models.CharField(max_length=50, null=True, blank=True)## 标记，主要是标记ansible的hosts中的哪一个组执行了这个规则
    i_tag = models.CharField(max_length=50, blank=True,default='新平台')## 标签
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
    ('MONEY-Black',u'现金网前端黑名单'),
    ('MN-Black',u'蛮牛前端黑名单'),
    ('api-bin',u'外接bbin白名单'),
    ('api-jdc',u'外接经典才白名单'),
    ('api-gfc',u'外接官方彩白名单'),
    )
    name = models.CharField(_(u'白名单配置'),max_length=25,choices=NAME,unique=True)
    servers = models.TextField(_(u'服务器地址'))
    file_path = models.CharField(_(u'文件绝对路径'),max_length=100)
    is_reload = models.BooleanField(_(u'是否重启'),default=False)
    hook = models.TextField(_(u'钩子'),null=True,blank=True)
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
    memo = models.TextField(_(u'备注'),default='')

class expiration_reminder(models.Model):
    """过期资产提醒,分为域名,证书,和服务器三个类别"""
    """到期前1个月提醒,alert为真,人工确认后alert为真,confirm为真,更新过期时间后重置判断条件"""
    ASSERT = (
    ('domain',u'域名'),
    ('certificate',u'证书'),
    ('server',u'服务器'),
    )
    classify = models.CharField(_(u'类型'),max_length=12,choices=ASSERT)
    text = models.TextField(_(u'内容'))
    is_alert = models.BooleanField(_(u'是否报警'),default=False)
    is_confirm = models.BooleanField(_(u'是否确认'),default=False)
    ctime = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField(_(u'过期时间'))

#------------------nginx访问控制系统表单设计---Header-------------------

class dsACL_TopProject(BaseModel):
    """顶级项目，下面设立子项目，子项目下面设立IP表"""
    name = models.CharField(_(u'项目名称'),max_length=64,unique=True)
    servers = models.TextField(_(u'服务器地址'),blank=True)
    filename = models.CharField(_(u'文件绝对路径'),max_length=100)
    rule = models.TextField(_(u'匹配规则'))
    limit = models.IntegerField(_(u'相同IP限制条目'),blank=False)
    exception = models.TextField(_(u'无限制IP'),blank=True)
    hook = models.TextField(_(u'钩子'),blank=True)
    remark = models.TextField(_(u'备注'))

    def __unicode__(self):
        return self.name

class dsACL_SubProject(BaseModel):
    """子项目，下面设立IP表"""
    name = models.CharField(_(u'项目名称'),max_length=64,unique=True)
    parentPro = models.ForeignKey(dsACL_TopProject)
    useParentConf = models.BooleanField(default=True)
    servers = models.TextField(_(u'服务器地址'),blank=True)
    filename = models.CharField(_(u'文件绝对路径'),max_length=100)
    rule = models.TextField(_(u'匹配规则'))
    hook = models.TextField(_(u'钩子'),blank=True)
    remark = models.TextField(_(u'备注'))

    def __unicode__(self):
        return self.name

class dsACL_ngx(BaseModel):
    """IP表，依附于子项目的配置"""
    host = models.GenericIPAddressField()
    project = models.ForeignKey(dsACL_SubProject)
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    ctime = models.DateTimeField(auto_now_add=True)
    remark = models.TextField(_(u'备注'))
    delTask = models.BooleanField(_(u'定时删除任务'),default=False)
    delDateTime = models.DateTimeField(_(u'定时删除时间'),blank=True,null=True)

    def getIgnoreList(self):
        return ['user']

    def __unicode__(self):
        return self.host

class pre_Add_acl(BaseModel):
    """预先添加的访问控制IP库，定时任务先把疑点IP存入此库，人工审核后同步数据到dsACL_ngx"""
    host = models.GenericIPAddressField() #IP地址ipv4 or ipv6
    count = models.IntegerField(default=0) #此IP违规访问的总次数
    status = models.BooleanField(default=True) #是否可以添加到dsACL_ngx里面，已存在的话此为False
    project = models.CharField(_(u'项目ID'),max_length=64) #此不用外键是为了避免强耦合，根据此项目ID来处理status字段
    ctime = models.DateTimeField(auto_now_add=True) #添加时间
    uptime = models.DateTimeField(auto_now=True) #更新时间

    def __unicode__(self):
        return self.host

class pre_Add_remark(BaseModel):
    """还是把日志数据分出来比较好，不和IP放一起"""
    host = models.ForeignKey(pre_Add_acl,related_name='filter_logs')
    server = models.GenericIPAddressField() #从这台服务器上提取到的IP
    filename = models.CharField(_(u'文件绝对路径'),max_length=100) #从这个文件里提取到的ip
    count = models.IntegerField(default=0) #触发配备规则的次数
    ctime = models.DateTimeField(auto_now_add=True) #添加时间
    remark = models.TextField() #主要存储从文件里过滤出来的语句，留作判断是不是真的违规ip

    def __unicode__(self):
        return self.host
#------------------nginx访问控制系统表单设计---Footer-------------------