#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import template

register = template.Library()

@register.filter(name='show_genxin_memo')
##顶一个接受server uuid的函数
def show_genxin_memo(memo):
    unicode_memo = memo.decode('utf-8')
    dict_memo = eval(unicode_memo)
    if dict_memo.has_key('common'):
        common = dict_memo['common']
    else:
        common = dict_memo['原因']
    env = dict_memo['env']
    method = dict_memo['method']
    if dict_memo.has_key('public_release'):
        pub = dict_memo['public_release']
    else:
        pub = '0'
    if dict_memo.has_key('web_release'):
        web = dict_memo['web_release']
    else:
        web = '0'
    content = u"环境："+env+'\t\r\n'+u" public版本号："+pub+'\t\r\n'+u" web版本号："+web+'\t\r\n'+u" 原因："+common
    return  content
