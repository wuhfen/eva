# -*- coding:utf-8 -*-
from django import forms

from business import models
from django.forms import ModelForm


class BusinessForm(ModelForm):
    class Meta:
        model = models.Business
        # fields = '__all__'
        # fields = ['full_name','name','nic_name','platform','initsite_data','functionary','ds_contact','agent_contact','agent_contact_method',
        #         'other_contact_method','status','status_update_date','front_station_web_dir','front_station_web_file','front_proxy_web_dir',
        #         'front_proxy_web_file','backend_station_web_dir','backend_station_web_file','backend_proxy_web_dir','backend_proxy_web_file',
        #         'third_proxy_web_dir','third_proxy_web_file','description']
        exclude = ['initsite_data','functionary','ds_contact','agent_contact','agent_contact_method','other_contact_method','status_update_date','reserve_a',
                    'reserve_b','reserve_c','reserve_d','reserve_e','reserve_f','create_date','update_date']


class DomainNameForm(ModelForm):
    class Meta:
        model = models.DomainName
        fields = '__all__'

class IPpoolForm(ModelForm):
    class Meta:
        model = models.Domain_ip_pool
        fields = '__all__'

class DnsApiForm(ModelForm):
    class Meta:
        model = models.dnsmanage_apikey
        fields = '__all__'

class DnsNameForm(ModelForm):
    class Meta:
        model = models.dnsmanage_name
        fields = '__all__'

class DnsRecordForm(ModelForm):
    class Meta:
        model = models.dnsmanage_record
        fields = '__all__'
