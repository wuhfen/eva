#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from business import models
# Register your models here.

class BusinessAdmin(admin.ModelAdmin):
    list_display =('name','nic_name','status','platform')

class BugsAdmin(admin.ModelAdmin):
    list_display =('bug_type','bug_name','bug_status','bug_level','issue_description','resolution_step')

class PlatformAdmin(admin.ModelAdmin):
    list_display =('name','status','description')

class DomainNameAdmin(admin.ModelAdmin):
    list_display =('name','business','status','status_code','address','supplier')


admin.site.register(models.Business,BusinessAdmin)
admin.site.register(models.Bugs,BugsAdmin)
admin.site.register(models.DomainName,DomainNameAdmin)
admin.site.register(models.Platform,PlatformAdmin)

