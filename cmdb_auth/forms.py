#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from cmdb_auth.models import user_auth_cmdb, auth_group
# from assets.models import project_swan

class cmdb_groupForm(forms.ModelForm):
    u"""定义权限组的表单"""
    enable = forms.TypedChoiceField(
                   coerce=lambda x: x == 'True',
                   choices=((True, '启用'), (False, '禁用')),
                   required=True, initial=True,
                   widget=forms.RadioSelect,
                   label=u"是否启用"
                )

    class Meta:
        model = auth_group
        fields = ["group_name", "explanation", "enable"]



class group_auth_addForm(forms.ModelForm):
    u"""给组赋予权限的表单"""

    class Meta:
        model = user_auth_cmdb

        fields = ["select_host", "add_host", "bat_add_host", "edit_host", "update_host", "delete_host",  "add_user",
                  "edit_user", "edit_pass", "delete_user", "add_department", "group_name", "add_idc", "edit_idc",
                  "del_idc", "setup_system", "upload_system", "salt_keys", "auth_log", "project_auth", "add_project",
                  "edit_project", "delete_project", "add_line_auth", "select_idc", "auth_project", "auth_highstate",
                  "cmdb_log", "server_audit"
                  ]

class auth_group_userForm(forms.ModelForm):
    u"""给组添加用户的表单"""
    class Meta:
        model = auth_group
        fields = ["group_user"]

# class auth_add_swan_user(forms.ModelForm):

#     class Meta:
#         model = project_swan
#         fields = ["push_user"]