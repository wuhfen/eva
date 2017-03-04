#!/usr/bin/env python
#coding:utf8
from opswiki.models import Category,Article

from django import forms
from django.forms import ModelForm
from pagedown.widgets import PagedownWidget




class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ArticleForm(ModelForm):
    body = forms.CharField(widget=PagedownWidget(show_preview=True))
    class Meta:
        model = Article
        exclude = ['author','change_date','date']