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
    ("huidu",u"灰度环境"),
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

class ScriptForm(ModelForm):
    name = forms.CharField(label=u'发布名称',widget=forms.TextInput(attrs={'placeholder': u'新站发布'}))
    command = forms.CharField(label=u'脚本执行路径',widget=forms.TextInput(attrs={'placeholder': '/bin/bash  /data/shell/newfabu.sh'}))
    server_ip = forms.CharField(label=u'脚本所在IP',widget=forms.TextInput(attrs={'placeholder': '需要CMDB里有此IP并且ansible可与其通信'}))
    memo = forms.CharField(label=u'描述简介',widget=forms.Textarea(attrs={'rows':5,'cols':30}))

    class Meta:
        model = models.scriptrepo
        fields = ['name','command','server_ip','custom_state','memo']