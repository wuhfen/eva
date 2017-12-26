#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from business import models
# Register your models here.
from .models import dnsmanage_apikey,dnsmanage_name, dnsmanage_record

class BusinessAdmin(admin.ModelAdmin):
    list_display =('name','nic_name','status','platform')


class DomainNameAdmin(admin.ModelAdmin):
    list_display =('name','business','supplier')


admin.site.register(models.Business,BusinessAdmin)
admin.site.register(models.DomainName,DomainNameAdmin)



class DnsApiAdmin(admin.ModelAdmin):
    model = dnsmanage_apikey
    exclude = ('remark',)

class DnsName(admin.ModelAdmin):
    model = dnsmanage_name
    exclude = ('remark',)

class DnsRecord(admin.ModelAdmin):
    model = dnsmanage_record
    exclude = ('remark',)


admin.site.register(dnsmanage_apikey,DnsApiAdmin)
admin.site.register(dnsmanage_name,DnsName)
admin.site.register(dnsmanage_record,DnsRecord)
