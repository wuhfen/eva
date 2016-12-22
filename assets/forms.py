#!/usr/bin/env python
#coding:utf8
from assets import models
from django import forms
from django.forms import ModelForm

class AssetForm(ModelForm):
    FAVORITE_COLORS_CHOICES = (
        ('serverhost', u'物理机'),
        ('virtual', u'虚拟机'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('firewall', u'防火墙'),
        ('storage', u'存储设备'),
        ('contain', u'Docker'),
        ('others', u'其它类'),
    )
    asset_number = forms.CharField(label=u'资产编号',required=False,widget=forms.TextInput(attrs={'placeholder': 'DT-server-20161014-001'}))
    asset_type = forms.CharField(label=u'资产类型',required=False,widget=forms.Select(attrs={'initial': 'serverhost','hidden': "hidden"}, choices=FAVORITE_COLORS_CHOICES))
    class Meta:
        model = models.Asset
        fields = '__all__'

class ServerForm(ModelForm):
    # ssh_password = forms.CharField(label=u'SHH密码',required=False,widget=forms.PasswordInput)
    class Meta:
        model = models.Server
        fields = ['name','ansible_name','ipmitool','ssh_user','ssh_host','ssh_port','ssh_password','parent','Raid_level','Disk_total','RAM_total','project','service','model','env',
                'os_kernel','Raid_level','system_status','os_type','os_version','os_release','server_sn','Services_Code','idc','cabinet','server_cabinet_id','old_ip']



class CPUForm(ModelForm):
    class Meta:
        model = models.CPU
        fields = ["cpu_model","cpu_count","cpu_core_count","memo"]

class RAMForm(ModelForm):
    capacity = forms.IntegerField(label=u'容量(GB)',required=True, widget=forms.TextInput(attrs={'placeholder': '必填项'}))
    class Meta:
        model = models.RAM
        fields = ["model","capacity","sn","slot","memo"]

class DiskForm(ModelForm):
    class Meta:
        model = models.Disk
        fields = ["sn","slot","iface_type","model","manufactory","capacity","memo"]

class NICForm(ModelForm):
    macaddress = forms.CharField(label=u'MAC地址',required=True, widget=forms.TextInput(attrs={'placeholder': '必填项'}))
    class Meta:
        model = models.NIC
        fields = ["name","model","macaddress","ipaddress","netmask","memo"]

class RaidForm(ModelForm):
    class Meta:
        model = models.RaidAdaptor
        fields = ["model","sn","slot","memo"]

class SQLpassForm(ModelForm):
    title = forms.CharField(label=u'应用版本',widget=forms.TextInput(attrs={'placeholder': 'mysql-5.6.0 or redis-2.3'}))
    listen = forms.CharField(label=u'监听地址',widget=forms.TextInput(attrs={'placeholder': '0.0.0.0'}))
    class Meta:
        model = models.sqlpasswd
        fields = '__all__'