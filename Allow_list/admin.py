#!/usr/bin/env python
# coding:utf-8

from django.contrib import admin
from .models import Iptables, oldsite_line,white_conf
from import_export import resources
from import_export import fields
from import_export.admin import ImportExportModelAdmin
from import_export.admin import ImportExportActionModelAdmin

# Register your models here.
class IptablesAdmin(admin.ModelAdmin):
    list_display = ('i_comment','i_source_ip','i_destination_ip','i_protocol','i_ports','i_states','i_target','i_date_time','i_user',)

class oldsite_lineAdmin(admin.ModelAdmin):
    list_display = ('host_ip','agent','line','number','status','comment','user','date_time')

class IPResource(resources.ModelResource):
    i_source_ip = fields.Field(column_name='VPN-IP', attribute='i_source_ip')
    i_comment = fields.Field(column_name='备注', attribute='i_comment')
    class Meta:
        model = Iptables
        fields = ('i_source_ip','i_comment')
        export_order = ('i_source_ip','i_comment')

class importIPtablesAdmin(ImportExportModelAdmin):
    resource_class = IPResource
    list_display = ('i_comment','i_source_ip','i_remark')

class exportIPtablesAdmin(ImportExportActionModelAdmin):
    resource_class = IPResource

admin.site.register(Iptables, importIPtablesAdmin)

class WhiteConfAdmin(admin.ModelAdmin):
    model = white_conf
    list_display = ('name','servers')

admin.site.register(white_conf, WhiteConfAdmin)
