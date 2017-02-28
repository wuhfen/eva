#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models 
from accounts.models import CustomUser as User
from assets.models import Server
import uuid
import datetime

import redisco
redisco.connection_setup(host='localhost', port=6379, db=1)

from redisco import models as re_models
class DomainInfo(re_models.Model):
    name = re_models.Attribute(required=True)
    created_at = re_models.DateTimeField(auto_now_add=True)
    res_code = re_models.IntegerField(default=0)
    alert = re_models.BooleanField(default=False)
    new_msg = re_models.BooleanField(default=True)
    address = re_models.ListField(str)
    info = re_models.Attribute()


class Platform(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=64, verbose_name=u"名称")
    nic_name = models.CharField(max_length=32, blank=True,verbose_name=u"代号")
    status = models.BooleanField(default=True,verbose_name=u"平台状态")

    front_station = models.ManyToManyField(Server, blank=True, related_name=u"front_station", verbose_name=u"前端源站")
    front_proxy = models.ManyToManyField(Server, blank=True, related_name=u"front_proxy", verbose_name=u"前端代理")
    front_image_site = models.ManyToManyField(Server, blank=True,related_name=u"front_image_site", verbose_name=u"前端图片站")
    front_download_site = models.ManyToManyField(Server, blank=True,related_name=u"front_download_site", verbose_name=u"前端下载站")
    front_active_site = models.ManyToManyField(Server, blank=True,related_name=u"front_active_site", verbose_name=u"前端动态资源处理站")
    front_active_cache = models.ManyToManyField(Server, blank=True,related_name=u"front_active_cache", verbose_name=u"前端动态资源缓存站")
    front_db_site = models.CharField(max_length=128,blank=True, verbose_name=u"前端数据库接口")
    front_cdn = models.CharField(max_length=100,blank=True, verbose_name=u"前端cdn")
    front_high_protection = models.CharField(max_length=100,blank=True, verbose_name=u"前端高防")

    backend_station = models.ManyToManyField(Server, blank=True, related_name=u"backend_station", verbose_name=u"后台源站")
    backend_proxy = models.ManyToManyField(Server, blank=True, related_name=u"backend_proxy", verbose_name=u"后台代理")
    backend_image_site = models.ManyToManyField(Server, blank=True,related_name=u"backend_image_site", verbose_name=u"后台图片站")
    backend_active_site = models.ManyToManyField(Server, blank=True,related_name=u"backend_active_site", verbose_name=u"后台动态资源处理站")
    backend_db_site = models.CharField(max_length=128,blank=True, verbose_name=u"后台数据库接口")

    third_party_node = models.ManyToManyField(Server, blank=True, related_name=u"third_party_node", verbose_name=u"第三方反代节点")




    description = models.TextField(blank=True, null=True, verbose_name=u'介绍')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,null=True, auto_now=True)
    class Meta:
        verbose_name = u'业务Platform'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name

class Business(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    full_name = models.CharField(max_length=128,blank=True, verbose_name=u"业务全名")
    name = models.CharField(max_length=64, blank=True,verbose_name=u"业务简称")
    nic_name = models.CharField(max_length=64,blank=True, verbose_name=u"发布代号")
    platform = models.ForeignKey(Platform,blank=True,null=True,on_delete=models.SET_NULL, verbose_name=u"平台")
    initsite_data = models.CharField(max_length=64,blank=True,verbose_name=u"建站时间")
    functionary = models.ForeignKey(User, related_name=u"functionary",blank=True, null=True,on_delete=models.SET_NULL, verbose_name=u"我司负责人", )
    ds_contact = models.ForeignKey(User, related_name=u"ds_contact",blank=True, null=True,on_delete=models.SET_NULL, verbose_name=u"我司专员", )
    agent_contact = models.CharField(max_length=100,blank=True, verbose_name=u"客户名")
    agent_contact_method = models.CharField(max_length=100,blank=True, verbose_name=u"客户电话")
    other_contact_method = models.CharField(max_length=100,blank=True, verbose_name=u"联系方式")
    SITE_STATUS_CHOICES = (
    ('0', u"正常运转"),
    ('1', u"维护升级"),
    ('2', u"迁移过渡"),
    ('3', u"停止运转"),
    )
    status = models.CharField(max_length=100,blank=True,choices=SITE_STATUS_CHOICES,verbose_name=u"业务状态")
    status_update_date = models.CharField(max_length=64,blank=True,verbose_name=u"状态变更时间")
    ##网站前端源站nginx配置
    front_station = models.TextField(blank=True, null=True, verbose_name=u"前端源站")
    front_station_web_dir = models.CharField(max_length=64,blank=True, verbose_name=u"前端web路径")
    front_station_web_file = models.CharField(max_length=64,blank=True, verbose_name=u"前端web文件")
    #网站前端nginx反向代理配置
    front_proxy = models.TextField(blank=True, null=True, verbose_name=u"前端代理")
    front_proxy_web_dir = models.CharField(max_length=64,blank=True, verbose_name=u"前端代理web路径")
    front_proxy_web_file = models.CharField(max_length=64,blank=True, verbose_name=u"前端代理web文件")
    ##管理后台路径
    backend_station = models.TextField(blank=True, null=True, verbose_name=u"后台源站")
    backend_station_web_dir = models.CharField(max_length=64,blank=True, verbose_name=u"后台web路径")
    backend_station_web_file = models.CharField(max_length=64,blank=True, verbose_name=u"后台web文件")
    ##后台nginx反代路径
    backend_proxy = models.TextField(blank=True, null=True,  verbose_name=u"后台代理")
    backend_proxy_web_dir = models.CharField(max_length=64,blank=True, verbose_name=u"后台代理web路径")
    backend_proxy_web_file = models.CharField(max_length=64,blank=True, verbose_name=u"后台代理web文件")
    ##第三方nginx反代配置
    third_party_node = models.TextField(blank=True, null=True,  verbose_name=u"第三方反代节点")
    third_proxy_web_dir = models.CharField(max_length=64,blank=True, verbose_name=u"三方反代web路径")
    third_proxy_web_file = models.CharField(max_length=64,blank=True, verbose_name=u"三方反代web文件")
    ##其他预留字段
    reserve_a = models.CharField(max_length=8,blank=True)
    reserve_b = models.CharField(max_length=8,blank=True)
    reserve_c = models.CharField(max_length=8,blank=True)
    reserve_d = models.CharField(max_length=8,blank=True)
    reserve_e = models.CharField(max_length=8,blank=True)
    reserve_f = models.CharField(max_length=8,blank=True)

    description = models.TextField(blank=True, null=True, verbose_name=u'备注')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, auto_now=True)
    class Meta:
        verbose_name = u'业务Business'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name





class DomainName(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=64, verbose_name=u"域名")
    DOMAIN_USE_CHOICES = (
    ('0', u"前端域名"),
    ('1', u"ag后台域名"),
    ('2', u"后台域名"),
    ('3', u"彩票域名"),
    ('4', u"导航网域名"),
    ('5', u"其他域名"),

    )
    use = models.CharField(max_length=64,blank=True, verbose_name=u"用途",choices=DOMAIN_USE_CHOICES)
    business = models.ForeignKey(Business,blank=True,null=True,on_delete=models.SET_NULL, verbose_name=u"所属业务")
    DOMAIN_STATUS_CHOICES = (
    ('0', u"备用"),
    ('1', u"再用"),
    ('2', u"弃用"),
    )
    state = models.CharField(max_length=64,blank=True, verbose_name=u"域名状态",choices=DOMAIN_STATUS_CHOICES)
    monitor_status = models.BooleanField(default=True,verbose_name=u"是否监控")
    # status_code = models.CharField(max_length=64,blank=True, verbose_name=u"状态码")
    address = models.ForeignKey('Domain_ip_pool',blank=True,null=True,on_delete=models.SET_NULL, verbose_name=u"解析到")
    # address = models.CharField(max_length=128,blank=True, verbose_name=u"绑定IP")

    # now_address = models.CharField(max_length=128,blank=True, verbose_name=u"解析IP")
    # analyze = models.CharField(max_length=128,blank=True, verbose_name=u"解析分析")
    DOMAIN_MANAGER =[(i, i) for i in (
    u"工程",
    u"运维",
    u"网站",
    u"其他",
    )]
    supplier = models.CharField(max_length=32,blank=True, verbose_name=u"管理者",choices=DOMAIN_MANAGER)
    description = models.TextField(blank=True, null=True, verbose_name=u'备注')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,null=True, auto_now=True)
    class Meta:
        verbose_name = u'域名DomainName'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name

class Domain_ip_pool(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    DOMAIN_IP_ATTR = [(i, i) for i in (u"自建高防（nginx反代）",u"CDN（抗攻击）",u"老站前端源站",u"老站后台反代",u"老站第三方ag反代",
        u"新站前端源站",u"新站后台反代",u"新站第三方ag反代",u"其他")]
    name = models.CharField(verbose_name=u"组名",max_length=32, blank=True,null=True,choices=DOMAIN_IP_ATTR)
    attribute = models.TextField(blank=True,verbose_name=u"IP列表")
    description = models.TextField(blank=True, null=True, verbose_name=u'备注')
    class Meta:
        verbose_name = u'域名IP池'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name


class Bugs(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    BUG_TYPE_CHOICES = (
    ('code_bug', u"代码bug"),
    ('intenet_bug', u"网络故障"),
    ('server_bug', u"服务器故障"),
    ('service_bug', u"应用服务故障"),
    ('preson_bug', u"误操作故障"),
    ('attack_bug', u"被攻击"),
    ('other_bug', u"其他"),
    )
    bug_type = models.CharField(max_length=64,choices=BUG_TYPE_CHOICES, verbose_name=u"故障类型")
    bug_name = models.CharField(max_length=64, verbose_name=u"故障名称")
    business = models.ManyToManyField(Business,blank=True,verbose_name=u"涉及业务")
    BUG_STATUS_CHOICES = (
    ('0', u"发现上报"),
    ('1', u"处理中"),
    ('2', u"已解决"),
    )
    bug_status = models.CharField(max_length=100,choices=BUG_STATUS_CHOICES,verbose_name=u"故障状态")
    BUG_LEVEL_CHOICES = (
    ('0', u"一般故障"),
    ('1', u"重要故障"),
    ('2', u"严重故障"),
    ('3', u"灾难故障"),
    )
    bug_level = models.CharField(max_length=100,choices=BUG_LEVEL_CHOICES,verbose_name=u"故障级别")
    bug_level_change = models.BooleanField(default=False, verbose_name=u"故障是否升级")
    appear_time = models.IntegerField(blank=True, null=True, verbose_name=u'出现次数')
    bug_assigned = models.ForeignKey(User, related_name=u"bug_assigned",blank=True, null=True, verbose_name=u"处理人员")
    bug_change_assigned = models.ForeignKey(User, related_name=u"bug_change_assigned",blank=True, null=True, verbose_name=u"转派人员")
    bug_tracker = models.ForeignKey(User, related_name=u"bug_tracker",blank=True, null=True, verbose_name=u"跟踪人员")
    bug_accept = models.BooleanField(default=False, verbose_name=u"是否接单")
    bug_assigned_change = models.BooleanField(default=False, verbose_name=u"是否转派")
    bug_solve = models.BooleanField(default=False, verbose_name=u"是否解决")
    issue_description = models.TextField(u'故障描述', null=True, blank=True)
    resolution_step = models.TextField(u'处理步骤', null=True, blank=True)
    change_reason = models.TextField(u'转派原因', null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        verbose_name = u'故障Bugs'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.bug_name










