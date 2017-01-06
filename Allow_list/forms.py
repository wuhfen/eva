# -*- coding:utf-8 -*-
from django import forms
from .models import Iptables

class IptablesForm(forms.Form):
    IPTABLE_CHOICES = [(i, i) for i in (u"鸿发Hongfa", u"澳门娱乐城Macau Entertainment City",u"一筒国际A tube of international",u"四季城Four Seasons City",u"金六福JLF",u"云顶至尊Genting Extreme",u"菁英会Elite Club",
    u"新濠天地City of Dreams",u"法拉利Ferrari",u"永利Wynn",u"金沙城Sands City",u"美高梅MGM",u"新葡京New Lisboa",u"澳门新葡京Macau Grand Lisboa",u"大发-酷客DAFA&KUKE",u"LV娱乐城Entertainment City",
    u"澳门国际Macau International",u"盛世国际Golden Age International",u"易发YIFA",u"菲律宾Philippines",u"诚信Integrity",u"博狗BOGOU",u"守信SHOUXIN",u"威尼斯人The Venetians",u"金宝博Jinbao Bo",u"MOA办公室",u"其他other" )]
    # class Meta:
    #     model = Iptables
    #     fields = '__all__'
    ipaddr = forms.GenericIPAddressField(max_length=15,initial='0.0.0.0',required=True,error_messages={'required': u'你没有填写ip'})
    customer = forms.CharField(widget=forms.Select(choices=IPTABLE_CHOICES),required=True,error_messages={'required': u'你没有选择客户名'})
    # remark = forms.CharField(max_length=50, required=False)
    # tag = forms.CharField(max_length=50)
    OPTIONS = (
            # ("old_new", u"全平台"),
            ("only_old", u"仅老平台old platform"),
            ("only_new", u"仅新平台new platform"),
            )
    background = forms.ChoiceField(widget=forms.RadioSelect,choices=OPTIONS,required=True,error_messages={'required': u'你没有选择后端平台'})

