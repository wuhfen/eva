#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import template
from accounts.models import department_Mode
from gitfabu.models import git_task_audit
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='auditor_uniq')
def auditor_uniq(objs):
    #去重功能
    users = []
    objects = []
    for i in objs:
        if not i.auditor in users:
            users.append(i.auditor)
            objects.append(i)
    return objects

@register.filter(name='audit_group')
def audit_group(objs):
    ff = list(set([i.audit_group_id for i in objs]))
    return ff

@register.simple_tag
def name_group(group_id):
    group = department_Mode.objects.get(pk=group_id)
    return group.name


@register.filter(name='audit_users')
def audit_users(objs):
    group = department_Mode.objects.get(pk=objs)
    ff = group.members.all()
    return ff

@register.simple_tag
def is_audit(group_id,user,objs):
    obj = objs.filter(auditor=user,audit_group_id=group_id)[0]
    if obj.isaudit:
        if obj.ispass:
            return '<span class="text-blue">%s已通过 </span>'% user
        else:
            return '<span class="text-red">%s未通过 </span>'% user
    else:
        return mark_safe('<span class="text-black">%s未审核 </span>'% user)