#!/usr/bin/env python
# -*- coding: utf-8 -*-

from accounts.models import department_Mode, department_auth_cmdb

def auth_class(user):
    """
    根据用户反向查找到所有的组，然后根据组权限返回一个dict，给用户session更新权限使用
    """
    res = {}
    if user:
        try:
            departments = user.group_users.all()
        except:
            return res
        for group in departments:
            print "%s你在此组：%s"% (user.first_name,group.name)
            try:
                auth_data = department_auth_cmdb.objects.get(department_name=group)
                auth_list = [f.name for f in auth_data._meta.get_fields() if f.name != "id"]  #排除id，给出权限列表
                auth_list.remove('department_name') #权限列表排除组名
                for i in auth_list:
                    s=getattr(auth_data,i)  #获取权限为真的字段
                    if s:res[i] = s
            except:
                pass
        print res
    return res

def myauth(request):
    """
    返回我的权限给settings模板全局变量，用于nav展示
    """
    return auth_class(request.user)
