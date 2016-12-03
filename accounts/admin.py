#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser, DepartmentGroup, department_Mode, server_auth
 # extend Django's built-in UserCreationForm and UserChangeForm to
 # remove the username field (and optionally add any others that are
 # required)

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserCreationForm, self).__init__(*args, **kargs)
        # del self.fields['username']

    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserChangeForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    def __init__(self, *args, **kargs):
        super(CustomUserChangeForm, self).__init__(*args, **kargs)
        # del self.fields['username']

    class Meta:
        model = CustomUser
        fields = '__all__'
# Register your models here.
class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name',
                                          'mobile', 'user_key', 'department')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}
        ),
    )
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('email', 'first_name', 'last_name',
                    'mobile',
                    'uuid',
                    'session_key',
                    'user_key',
                    'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'mobile')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(department_Mode)
admin.site.register(DepartmentGroup)
admin.site.register(server_auth)
admin.site.unregister(Group)
