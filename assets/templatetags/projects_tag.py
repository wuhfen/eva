#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast

from django import template
from assets.models import Server, Project

register = template.Library()

@register.filter(name='business_list')
##顶一个接受server uuid的函数
def business_list(host):
    cmdb_data = Server.objects.get(pk=host)
    data = cmdb_data.project.all()
##根据uuid获取server实例，然后找出实例中的项目实例
    project_all = []
    for i in data:
        project_all.append(i.project_name)
##定义一个数组，将项目实例的名称添加进去，返回项目名称的数组
    return project_all




# @register.filter(name='business_service')
# def business_service(name):
#     s = []
#     bus_data = Project.objects.get(service_name=name)
#     server_list = Host.objects.filter(business=bus_data).order_by("id")

#     for i in server_list:
#         t = i.service.all()
#         for b in t:
#             if b not in s:
#                 s.append(b)

#     return s


@register.filter(name='group_str2')
def groups_str2(group_list):
    if len(group_list) < 3:
        return ' '.join([group.name for group in group_list])
    else:
        return '%s ...' % ' '.join([group.name for group in group_list[0:2]])


# @register.filter(name='get_vm_info')
# def get_vm_info(host_id):
#     host = Host.objects.get(uuid=host_id)
#     vm = Host.objects.filter(vm=host)
#     if vm:
#         return vm
#     else:
#         return False

# @register.filter(name='str_to_list')
# def str_to_list(info):
#     return ast.literal_eval(info)