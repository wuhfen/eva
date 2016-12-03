#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models 
from accounts.models import CustomUser as User
from uuidfield import UUIDField
import datetime
import uuid

# 产品线包含多个相关项目，比如直播产品线
class Line(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=100, verbose_name=u"产品线")
    slug = models.TextField(max_length=128, blank=True, null=True, verbose_name=u"简介")
    sort = models.IntegerField(blank=True, null=True, default=0, verbose_name=u"排序")
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = u"产品线"
        verbose_name_plural = verbose_name

# 项目，包含多个资产，比如使用多少台服务器
class Project(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    project_name = models.CharField(max_length=60, blank=True, null=True, verbose_name=u'项目名')
    aliases_name = models.CharField(max_length=60, blank=True, null=True, verbose_name=u'别名，用于监控')
    project_contact = models.ForeignKey(User, related_name=u"main_business", verbose_name=u"负责人", )
    description = models.TextField(blank=True, null=True, verbose_name=u'项目介绍')
    line = models.ForeignKey(Line, null=True, blank=True, related_name=u"business", verbose_name=u"产品线", db_index=False,on_delete=models.SET_NULL)
    project_doc = models.TextField(blank=True, null=True, verbose_name=u'项目维护说明')
    project_user_group = models.TextField(blank=True, null=True, verbose_name=u'组成员', help_text=u"只有项目组成员才能申请发布")
    sort = models.IntegerField(blank=True, null=True, default=0, verbose_name=u"排序")
    def __unicode__(self):
        return self.project_name

    class Meta:
        verbose_name = u"项目"
        verbose_name_plural = verbose_name

# 项目组成员
# class ProjectUser(models.Model):
#     uuid = UUIDField(auto=True, primary_key=True)
#     project = models.ForeignKey(Project,db_index=False,default="")
#     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name=u"user")
#     data_created = models.DateTimeField(auto_now_add=True)
#     project_env = models.CharField(max_length=100, blank=True, null=True, verbose_name=u"项目环境")

#     def __unicode__(self):
#         return unicode(self.user.username)

#     class Meta:
#         verbose_name = u"项目组成员"
#         verbose_name_plural = verbose_name


#机房的哪个区域，关联一些机柜，关联机房
class Moudle(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    idc = models.ForeignKey('IDC',verbose_name='属于')
    name = models.CharField(u'机房模块',max_length=64,unique=True)
    memo = models.CharField(u'备注',max_length=128,blank=True,null=True)
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = '机房area'
        verbose_name_plural = verbose_name

#机柜表
class Cabinet(models.Model):
    '''
    在机房一般机柜都是关联模块的 模块就是指这个机柜在机房哪个区
    因为机柜可以没有IP,所以没有关联IP 等着被IP关联 因为IP属于交换机的一部分 交换机属于机柜
    '''
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    model = models.ForeignKey(Moudle,verbose_name='所属模块',related_name=u"FAN")
    name = models.CharField('机柜名称',max_length=64)
    brander = models.CharField('机柜品牌',max_length=64)
    # quantity = models.CharField('电量',max_length=64)
    # first_port = models.IntegerField('上联端口')
    # bandwidth = models.CharField('带宽',max_length=64)
    # put_position_choice = (
    #     ('forward', '正向摆放'),
    #     ('reverse','反向摆放'),
    # )
    # put_position = models.CharField('摆放规则',choices=put_position_choice,default='reverse',max_length=64)
    memo = models.CharField(u'备注',max_length=128,blank=True,null=True)
    def __unicode__(self):
        return  self.name
    class Meta:
        verbose_name = '机房cabinet'
        verbose_name_plural = verbose_name

class IDC(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=64,verbose_name=u'机房名称')
    contacts = models.CharField(verbose_name=u'机房负责人',max_length=64)
    idc_phone = models.IntegerField(verbose_name=u'机房电话')
    contacts_phone = models.IntegerField(verbose_name=u'负责人电话')
    idc_addr = models.CharField(verbose_name=u'机房地址', blank=True, null=True, max_length=128)
    bandwidth = models.CharField(verbose_name=u'机房带宽',blank=True, null=True, max_length=64)
    operator = models.CharField(verbose_name=u'机房运营商',max_length=32,null=True, blank=True,help_text=u'例如：电信 联通 教育网 长城宽带等,国外运行商不一样')
    memo = models.CharField(verbose_name=u'备注',max_length=128,blank=True,null=True)

    class Meta:
        verbose_name = u'IDC机房'
        verbose_name_plural = verbose_name
        app_label = 'assets'

    def __unicode__(self):
        return self.name


class Service(models.Model):
    """
    基础服务，如nginx, haproxy, php....
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=30, unique=True, verbose_name=u"服务名称",
                            help_text=u'用于服务的开启停止或重载，如: "service nginxd restart"')
    port = models.IntegerField(null=True, blank=True, verbose_name=u"端口")
    remark = models.TextField(null=True, blank=True, verbose_name=u"备注")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"运行服务"
        verbose_name_plural = verbose_name

## 资产的厂商名称和支持电话例如保修联系
class Manufactory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(u'厂商或供应商名称',max_length=64, unique=True)
    support_num = models.CharField(u'支持电话',max_length=30,blank=True)
    support_email = models.EmailField(u'厂商邮件',max_length=68,blank=True)
    memo = models.CharField(u'备注',max_length=128,blank=True)

    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = u'设备厂商或供应商'
        verbose_name_plural = verbose_name

# 资产的属性
class Asset(models.Model):
    asset_type_choices = (
        ('serverhost', u'物理机'),
        ('virtual', u'虚拟机'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('firewall', u'防火墙'),
        ('storage', u'存储设备'),
        ('contain', u'Docker'),
        ('others', u'其它类'),
    )
    Status_Status = (
        ('on','线上使用'),
        ('wait','线下闲置'),
        ('in','报废'),
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset_number = models.CharField(verbose_name=u'资产编号',max_length=128, blank=True)
    asset_type = models.CharField(verbose_name=u'资产类型',max_length=64, blank=True)
    purpose = models.CharField(max_length=64,null=True, blank=True,verbose_name=u'用途')
    status = models.CharField(choices=Status_Status,max_length=64,verbose_name = u'设备状态',default='on')
    manufactory = models.ForeignKey('Manufactory',verbose_name=u'供应商',null=True, blank=True)
    trade_date = models.CharField(u'购买时间',max_length=64,blank=True,default='2016-01-01')
    expire_date = models.CharField(u'保修期',max_length=64,blank=True,default='2016-01-01')
    price = models.FloatField(u'价格(元)',null=True, blank=True)
    price_total = models.IntegerField(u'续保次数',null=True, blank=True,help_text=u'如果是租的vps，计算每月续保可以算出成本')
    tags = models.ManyToManyField('Tags' ,blank=True)
    applicant = models.CharField(verbose_name=u'资产申请者',max_length=64,null=True, blank=True)
    manager = models.ForeignKey(User, verbose_name=u'资产管理员',null=True, blank=True)
    memo = models.TextField(u'备注', null=True, blank=True)
    mark = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, auto_now=True)
    class Meta:
        verbose_name = u'资产Asset'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.asset_number

#如果资产是服务器
class Server(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.OneToOneField('Asset')
    name = models.CharField(verbose_name=u"主机名",max_length=64)
    ssh_host = models.GenericIPAddressField(u'SSH地址', blank=True,null=True,help_text=u'一般填写外网IP')
    ssh_port = models.SmallIntegerField(u'SSH端口', blank=True,null=True,default='22')
    ssh_password = models.CharField(verbose_name=u"SSH密钥",max_length=100, blank=True)
    ipmitool = models.GenericIPAddressField(u'远控IP', blank=True,null=True)
    # #如果是虚拟机 那么他的宿主机是这个
    parent = models.ForeignKey('self',related_name='parent_server',blank=True,null=True,verbose_name=u"虚拟机父主机")
    model = models.CharField(u'品牌型号',max_length=128,null=True, blank=True )
    server_sn = models.CharField(verbose_name=u"SN编号", max_length=32, blank=True, null=True)
    Services_Code = models.CharField(max_length=16, blank=True, null=True, verbose_name=u"快速服务编码")
    #cpu 内存 网卡 raid卡 都是 这些关联他

    SERVER_STATUS = (
    (0, u"未安装系统"),
    (1, u"已安装系统"),
    )
    system_status = models.IntegerField(verbose_name=u"系统状态", choices=SERVER_STATUS,blank=True,null=True)
    SYSTEM_OS = [(i, i) for i in (u"Linux", u"Windows","unix")]
    os_type  = models.CharField(u"系统类型", max_length=32, choices=SYSTEM_OS, blank=True,null=True)
    SYSTEM_VERSION = [(i, i) for i in (u"CentOS",u"Ubuntu",u"Windows Server")]
    os_version =models.CharField(u'系统版本',max_length=64, choices=SYSTEM_VERSION,blank=True,null=True)
    SYSTEM_RELEASE = [(i, i) for i in ("5","6","7","12.04","14.04","16.04","2003","2008","2012","2016")]
    os_release  = models.CharField(u'系统版本号',max_length=64,choices=SYSTEM_RELEASE, blank=True,null=True)
    SYSTEM_KERNEL = [(i, i) for i in ("2.6.32","3.2.82","3.4.112","3.10.103","3.12.64","3.16.37","3.18.43","4.1.34","4.4.25","4.7.8","4.8.2")]
    os_kernel = models.CharField(u'系统内核',max_length=128,choices=SYSTEM_KERNEL,null=True, blank=True )
    Raid_level = models.CharField(u'冗余级别',max_length=8,null=True, blank=True )
    Disk_total = models.CharField(u'硬盘总容量(GB)',max_length=8,null=True, blank=True )
    RAM_total = models.CharField(u'内存总容量(GB)',max_length=8,null=True, blank=True )

    idc = models.ForeignKey(IDC, null=True,blank=True,verbose_name=u'机房', on_delete=models.SET_NULL)
    cabinet = models.ForeignKey(Cabinet, verbose_name=u'所属机柜',null=True, blank=True)
    server_cabinet_id = models.IntegerField(blank=True, null=True, verbose_name=u'机器位置')

    project = models.ManyToManyField(Project, blank=True, verbose_name=u'所属项目')
    service = models.ManyToManyField(Service, blank=True, verbose_name=u'运行服务')
    # 虚拟机vps需要写环境，例如阿里云
    ENVIRONMENT = [(i, i) for i in (u"aliyun", u"aws", u"Tencent", u"pub")]
    env = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"系统环境", choices=ENVIRONMENT)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,auto_now=True)
    class Meta:
        verbose_name = u'资产Server'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return ("主机名：%s | IP：%s")% (self.name, self.ssh_host)

# #如果资产是网络设备
# class NetworkDevice(models.Model):
#     uuid = UUIDField(auto=True, primary_key=True)
#     asset = models.OneToOneField('Asset')
#     vlan_ip = models.GenericIPAddressField(u'VlanIP',blank=True,null=True)
#     intranet_ip = models.GenericIPAddressField(u'内网IP',blank=True,null=True)
#     sn = models.CharField(u'SN号',max_length=128,unique=True)
#     model = models.CharField(u'型号',max_length=128,null=True, blank=True)
#     port_num = models.SmallIntegerField(u'端口个数',null=True, blank=True)
#     device_detail = models.TextField(u'设置详细配置',null=True, blank=True)
#     create_date = models.DateTimeField(auto_now_add=True)
#     update_date = models.DateTimeField(blank=True,null=True)
#     def __unicode__(self):
#         return  self.vlan_ip
#     class Meta:
#         verbose_name = '网络设备'
#         verbose_name_plural = "网络设备"

# cpu信息
class CPU(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.OneToOneField('Asset')
    cpu_model = models.CharField(u'CPU型号', max_length=128,blank=True)
    cpu_count = models.SmallIntegerField(u'物理cpu个数',blank=True,default='2')
    cpu_core_count = models.SmallIntegerField(u'cpu核数',blank=True,default='2')
    memo = models.CharField(u'备注', max_length=128,null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,auto_now=True)

    class Meta:
        verbose_name = u'服务器CPU'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.cpu_model

# 内存信息
class RAM(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True,null=True)
    model =  models.CharField(u'内存型号', max_length=128, blank=True,null=True)
    slot = models.CharField(u'插槽', max_length=64, blank=True,null=True)
    capacity = models.IntegerField(u'内存大小(GB)')
    memo = models.CharField(u'备注',max_length=128, blank=True,null=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,null=True)
    auto_create_fields = ['sn','slot','model','capacity']

    def __unicode__(self):
        return ("%s型号_%sG大小")% (self.model, self.capacity)
    class Meta:
        verbose_name = u'服务器RAM'
        verbose_name_plural = verbose_name
        unique_together = ("asset", "slot")

# 硬盘信息
class Disk(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True,null=True)
    slot = models.CharField(u'插槽位',max_length=64, blank=True,null=True)
    manufactory = models.CharField(u'制造商', max_length=64,blank=True,null=True)
    model = models.CharField(u'磁盘型号', max_length=128,blank=True,null=True)
    capacity = models.FloatField(u'磁盘容量GB')
    disk_iface_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD'),
    )
    iface_type = models.CharField(u'接口类型', max_length=64,choices=disk_iface_choice,default='SAS')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True,auto_now=True)
    memo = models.CharField(u'备注',max_length=128, blank=True,null=True)
    auto_create_fields = ['sn','slot','manufactory','model','capacity','iface_type']

    def __unicode__(self):
        return ("%s型号_%sG大小_%s接口")% (self.model, self.capacity,self.iface_type)
    class Meta:
        verbose_name = u'服务器DISK'
        verbose_name_plural = verbose_name


# 网卡信息
class NIC(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.ForeignKey('Asset')
    name = models.CharField(u'网卡名', max_length=64, blank=True,null=True)
    sn = models.CharField(u'SN号', max_length=128, blank=True,null=True)
    model =  models.CharField(u'网卡型号', max_length=128, blank=True,null=True)
    macaddress = models.CharField(u'MAC', max_length=64, blank=True)
    ipaddress = models.GenericIPAddressField(u'IP', blank=True,null=True)
    netmask = models.CharField(verbose_name='子网掩码',max_length=64,blank=True,null=True)
    bonding = models.CharField(max_length=64,blank=True,null=True)
    memo = models.CharField(u'备注',max_length=128, blank=True,null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True,null=True)
    mark = models.BooleanField(default='False')
    auto_create_fields = ['name','sn','model','macaddress','ipaddress','netmask','bonding','mark']
    #auto_create_fields 定义这个表需要的数据 用于更新资产信息
    #我从例如json里 取出我这个表需要的key 之后插入到dataset里
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = u'服务器NIC'
        verbose_name_plural = verbose_name

# raid卡信息
class RaidAdaptor(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True,null=True)
    slot = models.CharField(u'插口',max_length=64, blank=True)
    model = models.CharField(u'型号', max_length=64,blank=True,null=True)
    memo = models.TextField(u'备注', blank=True,null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True,null=True)

    def __unicode__(self):
        return self.model
    class Meta:
        verbose_name = u'服务器Raid卡'
        verbose_name_plural = verbose_name


## 资产标签
class  Tags(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(verbose_name='标签名',max_length=32, unique=True)
    creater = models.ForeignKey(User)
    create_date = models.DateField(auto_now_add=True)
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = '资产Tag'
        verbose_name_plural = verbose_name
