#!/usr/bin/env python
# coding:utf-8

from django.contrib import admin
from .models import Iptables, oldsite_line
# Register your models here.
class IptablesAdmin(admin.ModelAdmin):
	list_display = ('i_comment','i_source_ip','i_destination_ip','i_protocol','i_ports','i_states','i_target','i_date_time','i_user',)

class oldsite_lineAdmin(admin.ModelAdmin):
	list_display = ('host_ip','agent','line','number','status','comment','user','date_time')

		
admin.site.register(oldsite_line,oldsite_lineAdmin)
admin.site.register(Iptables,IptablesAdmin)
