#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models
from automation.models import gengxin_deploy

from accounts.models import CustomUser as Users
import uuid

# Create your models here.
class ops_command_log(models.Model):
    #运维审计日志
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    start_time = models.CharField(_(u'开始时间'),max_length=64)
    end_time = models.CharField(_(u'结束时间'),max_length=64)
    command = models.TextField(_(u'内容'))
    user = models.ForeignKey(Users,verbose_name=u'用户')

    class Meta:
        verbose_name = u'运维审计日志'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name


class task_audit(models.Model):
    name = models.CharField(_(u'名称'),max_length=64)
    initiator = models.ForeignKey(Users,verbose_name=u'发起人',related_name="init")
    auditor = models.ForeignKey(Users,verbose_name=u'审核人',related_name="audi")
    create_date = models.DateTimeField(auto_now_add=True)
    memo = models.TextField(_(u'内容'))
    isaudit = models.BooleanField(_(u'是否审核'),default=False)
    ispass = models.BooleanField(_(u'是否通过'),default=False)
    audit_time = models.CharField(_(u'审核时间'),null=True,blank=True,max_length=64)
    postil = models.TextField(_(u'批注'),null=True,blank=True)
    loss_efficacy = models.BooleanField(_(u'是否过期'),default=False)
    gengxin = models.ForeignKey(gengxin_deploy,null=True,blank=True)

    class Meta:
        verbose_name = u'任务审核'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name