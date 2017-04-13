#!/usr/bin/env python
#coding:utf8
from assets.models import publickey,zabbixagent,basepkg
from django.forms import ModelForm

class pubkeyForm(ModelForm):
    class Meta:
        model = publickey
        exclude = ()

class zabbixagentForm(ModelForm):
    class Meta:
        model = zabbixagent
        exclude = ()

class basepkgForm(ModelForm):
    """docstring for basepkgForm"""
    class Meta:
        model = basepkg
        exclude = ()