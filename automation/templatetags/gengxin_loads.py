#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.filter(name='show_audit_memo')
##顶一个接受server uuid的函数
def show_audit_memo(memo):
    try:
        unicode_memo = memo.decode('utf-8')
    except AttributeError:
        return ""
    list_memo = eval(unicode_memo)
    com_list = []
    for i in list_memo:
        if i['isaudit'] == True and i['ispass'] == False:
            common = i['user']+u"未通过  原因："+i['postil']+u"  时间："+i['date']
            com_list.append(common)
        elif i['isaudit'] == True and i['ispass'] == True:
            common = i['user']+u"已通过  时间："+i['date']
            com_list.append(common)
        else:
            common = i['user']+u"未审核"
            com_list.append(common)

    return  "@".join(com_list)