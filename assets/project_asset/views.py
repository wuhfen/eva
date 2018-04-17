#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect,JsonResponse
from .forms import ProjectForm, ServiceForm
from assets.models import Project, Service, Server

def sort_project(project):
    sort = project.sort
    print "组%s 层级为%s"% (project.project_name,sort)
    print "开始给 %s组的子组排序"% project.project_name
    data = Project.objects.filter(parent=project)
    if data:
        data.update(sort=sort+1)
        for i in data:
            sort_project(i)
    else:
        print "组%s 没有子组，结束递归"% project.project_name



##项目信息
def project_add(request):
    pf = ProjectForm()
    if request.method == 'POST':
        sort = 0
        name = request.POST.get('project_name')
        if Project.objects.filter(project_name=name): 
            return JsonResponse({'result':"Repeated"},safe=False)
        parent_id = request.POST.get('parent')
        if parent_id:
            parent = Project.objects.get(pk=parent_id)
            parent_sort = parent.sort
            sort = int(parent_sort) + 1
            print sort
        else:
            parent = None
        data = Project(project_name=name,sort=sort,parent=parent)
        data.save()
        return JsonResponse({'result':"SUCCESS"},safe=False)
    return render(request,'assets/project_add.html',locals())


def project_list(request):
    data = Project.objects.all()
    return render(request,'assets/project_list.html',locals())

def project_rename(request):
    if request.method == 'POST':
        name = request.POST.get('project_name')
        uuid = request.POST.get('uuid')
        if Project.objects.filter(project_name=name): return JsonResponse({'result':"Repeated"})
        data = Project.objects.filter(pk=uuid)
        data.update(project_name=name)
        return JsonResponse({'result':"SUCCESS"})
    return JsonResponse({'result':"Error method"})

def project_reparent(request):
    '''重新给project或者server分配父组'''
    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        pid = request.POST.get('pid')
        isproject = request.POST.get('isproject')
        if pid != 'null':
            print "有PID，可以迁移"
            parent = Project.objects.get(pk=pid)
            if isproject == "yes":
                print "project迁移"
                children = Project.objects.filter(pk=uuid)
                children.update(parent=parent)
            else:
                print "server迁移"
                children = Server.objects.get(pk=uuid)
                children.project.add(parent)
                children.save()
    return JsonResponse({"res":"OK"})



def project_edit(request,uuid):
    """本组的父组选项中应该过滤掉自己的子组，否则会引起递归错误"""
    project_data = Project.objects.get(pk=uuid)
    pf = ProjectForm(instance=project_data)
    sort = project_data.sort

    data = Project.objects.filter(sort__lte=int(sort)).exclude(uuid=uuid) #层级小于等于本组层级的都可以设置为父组,排除自己
    if request.method == 'POST':
        sort = 0
        name = request.POST.get('project_name')
        parent_id = request.POST.get('parent')
        if parent_id:
            parent = Project.objects.get(pk=parent_id)
            parent_sort = parent.sort
            sort = int(parent_sort) + 1
            print sort
        else:
            parent = None
        Project.objects.filter(pk=uuid).update(project_name=name,sort=sort,parent=parent)
        sort_project(Project.objects.get(pk=uuid))
        return JsonResponse({'res':"OK"},safe=False)
    return render(request,'assets/project_edit.html', locals())


def project_delete(request, uuid):
    project_data = Project.objects.get(pk=uuid)
    parent = project_data.parent
    children = Project.objects.filter(parent=project_data)
    if children:
        if parent:
            children.update(parent=parent)
    project_data.delete()
    return JsonResponse({"result":"SUCCESS"})
    # return HttpResponseRedirect("/assets/project_list/")

##系统服务信息

def service_add(request):
    lf = ServiceForm()
    if request.method == 'POST':
        lf = ServiceForm(request.POST)
        if lf.is_valid():
            result = lf.save(commit=False)
            result.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/service_add.html',locals())


def service_delete(request, uuid):
    service_data = Service.objects.get(pk=uuid)
    service_data.delete()
    return HttpResponseRedirect("/assets/service_list/")


def service_list(request):
    data = Service.objects.all()
    return render(request,'assets/service_list.html',locals())


def service_edit(request,uuid):
    service_data = Service.objects.get(pk=uuid)
    if request.method == 'POST':
        lf = ServiceForm(request.POST, instance=service_data)
        
        if lf.is_valid():
            result = lf.save()
            return HttpResponseRedirect('/assets/service_list/')
    else:
        lf = ServiceForm(instance=service_data)
    return render(request,'assets/service_edit.html', locals())