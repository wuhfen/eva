#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from assets import  models
# Register your models here.
class ServerInline(admin.TabularInline):
    model = models.Server
    exclude = ('memo',)
    readonly_fields = ['create_date']

class ServerAdmin(admin.ModelAdmin):
    model = models.Server
    list_display = ('name','ipmitool','idc','cabinet','server_cabinet_id','asset','model','os_kernel','Raid_level','system_status','os_type',
                    'os_version','os_release','server_sn','Services_Code')
    # raw_id_fields = ('idc',)

##<class 'assets.admin.ServerAdmin'>: (admin.E109) The value of 'list_display[15]' must not be a ManyToManyField.

# 服务器
admin.site.register(models.Server,ServerAdmin)



class CPUInline(admin.TabularInline):
    model = models.CPU
    exclude = ('memo',)
    readonly_fields = ['create_date']

class NICInline(admin.TabularInline):
    model = models.NIC
    exclude = ('memo',)
    readonly_fields = ['create_date']

class RAMInline(admin.TabularInline):
    model = models.RAM
    exclude = ('memo',)
    readonly_fields = ['create_date']

class DiskInline(admin.TabularInline):
    model = models.Disk
    exclude = ('memo',)
    readonly_fields = ['create_date']

class AssetAdmin(admin.ModelAdmin):
#    list_display = ('asset_type','purpose','sn','manufactory','management_address','trade_date','expire_date','price',
#                    'price_total','admin','Services_Code','cabinet','server_cabinet_id','status')
    list_display = ('asset_type','purpose','asset_number','manufactory','expire_date','trade_date','price','manager','status')
    inlines = [ServerInline,CPUInline,NICInline,RAMInline,DiskInline]

# 资产
admin.site.register(models.Asset,AssetAdmin)   
# 产品线
admin.site.register(models.Line)
# 项目
admin.site.register(models.Project)
# 服务
admin.site.register(models.Service)
# admin.site.register(models.ProjectUser)

class CPUadmin(admin.ModelAdmin):
    list_display =('cpu_model','cpu_count','cpu_core_count','memo')
#cpu
admin.site.register(models.CPU,CPUadmin)

class NICadmin(admin.ModelAdmin):
    list_display =('asset','name','memo','model','macaddress','ipaddress','mark')
#网卡
admin.site.register(models.NIC,NICadmin)
#raid
admin.site.register(models.RaidAdaptor)
#内存
class RAMadmin(admin.ModelAdmin):
    list_display =('asset','model','capacity','slot','sn','memo')
admin.site.register(models.RAM,RAMadmin)
#IP
#硬盘
admin.site.register(models.Disk)

admin.site.register(models.Manufactory)
# #

# #网络设备
# admin.site.register(models.NetworkDevice)



class MoudleInline(admin.TabularInline):
    model = models.Moudle
    extra = 2
    exclude = ('memo',)

class CabinetInline(admin.TabularInline):
    model = models.Cabinet
    exclude = ('memo',)

class MoudleAdmin(admin.ModelAdmin):
    list_display = ('name','memo',)
    inlines = [CabinetInline,]

#机房
class IdcAdmin(admin.ModelAdmin):
    list_display = ('name','contacts','idc_phone','idc_addr','operator','memo')
    inlines = [MoudleInline,]
#机房表
admin.site.register(models.IDC,IdcAdmin)
#机房模块
admin.site.register(models.Moudle,MoudleAdmin)
#机柜表
admin.site.register(models.Cabinet)

#标签
admin.site.register(models.Tags)