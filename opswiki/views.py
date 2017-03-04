#!/usr/bin/env python
#coding:utf8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from opswiki.models import Category,Article
from opswiki.forms import ArticleForm
from django.http import JsonResponse

import time
import json

def list_article(request):
    obj = Article.objects.all()
    return render(request,'opswiki/list_article.html',locals())

def show_article(request,id):
    obj = Article.objects.get(pk=id)
    return render(request,'opswiki/show_article.html',locals())

def write_article(request):
    cateobj = Category.objects.all()
    af = ArticleForm()
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')

        if title and category_id:
            category = Category.objects.get(pk=category_id)
            author = request.user.username
            body = request.POST.get('body')
            change_date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            new_article = Article(category=category,title=title,author=author,body=body,change_date=change_date)
            new_article.save()
            return HttpResponseRedirect('/opswiki/article/list/')

    return render(request,'opswiki/write_article.html',locals())

def edit_article(request,id):
    cateobj = Category.objects.all()
    obj = Article.objects.get(pk=id)
    af = ArticleForm(instance=obj)
    if request.method == 'POST':
        af = ArticleForm(request.POST,instance=obj)
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        category = Category.objects.get(pk=category_id)
        body = request.POST.get('body')
        print body
        change_date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

        if af.is_valid():
            new_article = Article.objects.filter(pk=id)
            new_article.update(category=category,title=title,body=body,change_date=change_date)
            urls = "/opswiki/article/show/" + str(id)
            return HttpResponseRedirect(urls)
    return render(request,'opswiki/edit_article.html',locals())

# Create your views here.
