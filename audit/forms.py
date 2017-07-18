#!/usr/bin/env python
#coding:utf8
from audit import models
from automation.models import AUser
from django import forms
from django.forms import ModelForm

class RecordOPSForm(ModelForm):
    class Meta:
        model = models.ops_command_log
        fields = ['start_time','end_time','command']

class audituserForm(ModelForm):
    class Meta:
        model = AUser
        fields = ['name','user']