#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import admin
from opswiki.models import Category,Article
class CategoryAdmin(admin.ModelAdmin):
    model = Category

admin.site.register(Category,CategoryAdmin)
# Register your models here.
class ArticleAdmin(admin.ModelAdmin):
    model = Article

admin.site.register(Article,ArticleAdmin)