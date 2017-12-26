#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from gitfabu import models

class AuditorAdmin(admin.ModelAdmin):
    list_display =('platform','classify','isurgent','name','ischeck','start_time','end_time','manager')

admin.site.register(models.git_deploy_audit,AuditorAdmin)

class OpsAdmin(admin.ModelAdmin):
    list_display =('name','platform','classify')
admin.site.register(models.git_ops_configuration,OpsAdmin)

class DeployAdmin(admin.ModelAdmin):
    list_display = ('name','platform','classify')
admin.site.register(models.git_deploy,DeployAdmin)

class CodeAdmin(admin.ModelAdmin):
    list_display = ('title','platform','classify')
admin.site.register(models.git_coderepo,CodeAdmin)

class MytaskAdmin(admin.ModelAdmin):
    list_display = ('name','table_name','status','isend','memo','loss_efficacy')
admin.site.register(models.my_request_task,MytaskAdmin)

class UpdateAdmin(admin.ModelAdmin):
    list_display = ('name','method','memo','isuse','islog')
admin.site.register(models.git_code_update,UpdateAdmin)
