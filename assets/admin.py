#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from assets import  models
from assets.models import Server
from import_export import resources
from import_export import fields
from import_export.admin import ImportExportModelAdmin
from import_export.admin import ImportExportActionModelAdmin

# Register your models here.
# 服务器
class ServerInline(admin.TabularInline):
    model = Server
    exclude = ('memo',)
    readonly_fields = ['create_date']

class ServerAdmin(admin.ModelAdmin):
    model = Server
    list_display = ('ssh_host','ssh_port')
    # raw_id_fields = ('idc',)
admin.site.register(models.Server,ServerAdmin)

##数据导出admin
class ServerResource(resources.ModelResource):
    name = fields.Field(column_name='主机名', attribute='name') 
    ssh_host = fields.Field(column_name='IP地址', attribute='ssh_host')
    ssh_user = fields.Field(column_name='用户名', attribute='ssh_user')
    ssh_port = fields.Field(column_name='端口',attribute='ssh_port')
    ssh_password = fields.Field(column_name='密码',attribute='ssh_password')
    purpose = fields.Field(column_name='用途',attribute='asset__purpose')
    class Meta:
        model = Server
        #定义导出excel有那些列
        fields = ('name', 'ssh_host','ssh_user','ssh_port','ssh_password','purpose')
        #定义导出excel类的顺序
        export_order = ('name', 'ssh_host','ssh_user','ssh_port','ssh_password','purpose')

class importServerAdmin(ImportExportModelAdmin):
    resource_class = ServerResource

class exportServerAdmin(ImportExportActionModelAdmin):
    resource_class = ServerResource

# admin.site.register(Server, importServerAdmin)


class CPUInline(admin.TabularInline):
    model = models.CPU
    exclude = ('memo',)
    readonly_fields = ['create_date']

class NICInline(admin.TabularInline):
    model = models.NIC
    exclude = ('memo',)
    readonly_fields = ['name']

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
    list_display = ('asset_type','purpose','expire_date','status')
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
    list_display =('asset','name','ipaddress')
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

#权限
class SqlAdmin(admin.ModelAdmin):
    list_display = ('server','title','listen','port','user','password','memo')
admin.site.register(models.sqlpasswd,SqlAdmin)

