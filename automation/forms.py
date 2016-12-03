#!/usr/bin/env python
#coding:utf8
from automation import models
from django import forms
from django.forms import ModelForm


class ToolsForm(ModelForm):
    class Meta:
        model = models.Tools
        fields = '__all__'

class ConfileFrom(ModelForm):
    ENVIRONMENT_SELECT = (
    ("production",u"线上环境"),
    ("test",u"测试环境"),
    )
    name = forms.CharField(label=u'发布标题',widget=forms.TextInput(attrs={'placeholder': 'EX：新易发web主站'}))

    # environment = forms.CharField(label=u'资产编号',widget=forms.Select(choices=ENVIRONMENT_SELECT))
    # asset_number = forms.CharField(label=u'资产编号',widget=forms.TextInput(attrs={'placeholder': 'DT-server-20161014-001'}))
    # asset_number = forms.CharField(label=u'资产编号',widget=forms.TextInput(attrs={'placeholder': 'DT-server-20161014-001'}))
    class Meta:
        model = models.Confile
        fields = '__all__'

class DeployForm(ModelForm):
    class Meta:
        model = models.deploy
        fields = '__all__'