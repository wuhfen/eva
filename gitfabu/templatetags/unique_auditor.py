#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import template
from gitfabu.models import git_task_audit

register = template.Library()

@register.filter(name='auditor_uniq')
def auditor_uniq(objs):
    users = []
    objects = []
    for i in objs:
        if not i.auditor in users:
            users.append(i.auditor)
            objects.append(i)
    return objects