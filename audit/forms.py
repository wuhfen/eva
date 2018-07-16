#!/usr/bin/env python
#coding:utf8
from audit.models import ops_command_log,sql_conf
from django.forms import ModelForm

class RecordOPSForm(ModelForm):
    class Meta:
        model = ops_command_log
        fields = ['start_time','end_time','command']

class SqlConfForm(ModelForm):
    class Meta:
        model = sql_conf
        fields = '__all__'
