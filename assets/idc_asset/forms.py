#!/usr/bin/env python
#coding:utf8
from assets.models import IDC,Moudle,Cabinet
from django.forms import ModelForm

class IDCForm(ModelForm):
    class Meta:
        model = IDC
        exclude = ()

class MoudleForm(ModelForm):
    class Meta:
        model = Moudle
        exclude = ()

class CabinetForm(ModelForm):
    class Meta:
        model = Cabinet
        exclude = ()