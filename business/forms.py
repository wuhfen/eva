# -*- coding:utf-8 -*-
from django import forms

from business import models
from django.forms import ModelForm


class BusinessForm(ModelForm):
    class Meta:
        model = models.Business
        # fields = '__all__'
        fields = ['full_name','name','nic_name','platform','initsite_data','functionary','ds_contact','agent_contact','agent_contact_method',
                'other_contact_method','status','status_update_date','front_station_web_dir','front_station_web_file','front_proxy_web_dir',
                'front_proxy_web_file','backend_station_web_dir','backend_station_web_file','backend_proxy_web_dir','backend_proxy_web_file',
                'third_proxy_web_dir','third_proxy_web_file','description']


class PlatfForm(ModelForm):
    class Meta:
        model = models.Platform
        # fields = '__all__'
        fields = ['name','nic_name','status','front_station','front_proxy','front_image_site','front_download_site','front_active_site','front_active_cache','front_db_site',
                'front_cdn','front_high_protection','backend_station','backend_proxy','backend_image_site','backend_active_site','backend_db_site','third_party_node',
                'description']

class DomainNameForm(ModelForm):
    class Meta:
        model = models.DomainName
        fields = '__all__'
