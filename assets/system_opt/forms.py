#!/usr/bin/env python
#coding:utf8
from assets.models import publickey,zabbixagent
from django.forms import ModelForm

class pubkeyForm(ModelForm):
    class Meta:
        model = publickey
        exclude = ()

class zabbixagentForm(ModelForm):
    class Meta:
        model = zabbixagent
        exclude = ()