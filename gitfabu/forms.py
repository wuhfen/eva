#!/usr/bin/python
#-*-coding:utf-8-*-

from django import forms
from .models import git_deploy_audit
# from cmdb_auth.models import AuthNode
# from assets.models import project_swan, Host

class git_deploy_audit_from(forms.ModelForm):

    class Meta:
        model = git_deploy_audit
        fields = ["platform", "classify", "isurgent", "name","ischeck","start_time","end_time","user","group","manager"]