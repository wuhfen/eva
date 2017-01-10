#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models
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