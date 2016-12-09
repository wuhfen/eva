# -*- coding:utf-8 -*-
from django import forms
from .models import Iptables

class IptablesForm(forms.Form):
    IPTABLE_CHOICES = [(i, i) for i in (u"鸿发", u"澳门娱乐城",u"一筒国际",u"四季城",u"金六福",u"云顶至尊",u"菁英会",u"新濠天地",u"法拉利",u"永利",u"金沙城",
    u"美高梅",u"新葡京",u"澳门新葡京",u"大发-酷客",u"LV娱乐城",u"澳门国际",u"盛世国际",u"易发",u"菲律宾",u"诚信",u"博狗",u"守信",u"威尼斯人",u"金宝博",u"MOA办公室",u"其他" )]
    # class Meta:
    #     model = Iptables
    #     fields = '__all__'
    ipaddr = forms.GenericIPAddressField(max_length=15,initial='0.0.0.0',required=True,error_messages={'required': u'你没有填写ip'})
    comment = forms.CharField(widget=forms.Select(choices=IPTABLE_CHOICES),required=True,error_messages={'required': u'你没有选择客户名'})
    # remark = forms.CharField(max_length=50, required=False)
    # tag = forms.CharField(max_length=50)
    OPTIONS = (
            # ("old_new", u"全平台"),
            ("only_old", u"仅老平台"),
            ("only_new", u"仅新平台"),
            )
    remark = forms.ChoiceField(widget=forms.RadioSelect,choices=OPTIONS,required=True,error_messages={'required': u'你没有选择后端平台'})

