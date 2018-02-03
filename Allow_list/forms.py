# -*- coding:utf-8 -*-
from django import forms
from .models import white_conf

class WhiteConfForm(forms.ModelForm):
    class Meta:
        model = white_conf
        fields = ['name','servers','file_path','is_reload']