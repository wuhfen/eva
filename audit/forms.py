#!/usr/bin/env python
#coding:utf8
from audit import models
from django import forms
from django.forms import ModelForm

class RecordOPSForm(ModelForm):
    class Meta:
        model = models.ops_command_log
        fields = ['start_time','end_time','command']