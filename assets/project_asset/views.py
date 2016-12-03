#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from .forms import LineForm, ProjectForm, ServiceForm
from assets.models import Line,Project, Service
from accounts.models import CustomUser, department_Mode

##产品线信息
@permission_required('assets.Can_add_Line', login_url='/auth_error/')
def line_add(request):
	lf = LineForm()
	if request.method == 'POST':
		lf = LineForm(request.POST)
		if lf.is_valid():
			result = lf.save(commit=False)
			result.save()
			return HttpResponseRedirect('/allow/welcome/')
	return render(request,'assets/line_add.html',locals())

@permission_required('assets.Can_delete_Line', login_url='/auth_error/')
def line_delete(request, uuid):
    line_data = Line.objects.get(pk=uuid)
    line_data.delete()
    return HttpResponseRedirect("/assets/line_list/")

@permission_required('assets.Can_add_Line', login_url='/auth_error/')
def line_list(request):
	data = Line.objects.all()
	return render(request,'assets/line_list.html',locals())

@permission_required('assets.Can_add_Line', login_url='/auth_error/')
def line_edit(request,uuid):
    project_data = Line.objects.get(pk=uuid)
    if request.method == 'POST':
        lf = LineForm(request.POST, instance=project_data)
        
        if lf.is_valid():
            result = lf.save()
            return HttpResponseRedirect('/assets/line_list/')
    else:
        lf = LineForm(instance=project_data)
    return render(request,'assets/line_edit.html', locals())


##项目信息
@permission_required('assets.Can_add_project', login_url='/auth_error/')
def project_add(request):
    pf = ProjectForm()
    if request.method == 'POST':
        pf = ProjectForm(request.POST)
        if pf.is_valid():
            pf.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/project_add.html',locals())

@permission_required('assets.Can_add_project', login_url='/auth_error/')
def project_list(request):
    data = Project.objects.all()
    return render(request,'assets/project_list.html',locals())

@permission_required('assets.Can_add_project', login_url='/auth_error/')
def project_edit(request,uuid):
    project_data = Project.objects.get(pk=uuid)
    if request.method == 'POST':
        pf = ProjectForm(request.POST, instance=project_data)
        if pf.is_valid():
            pf.save()
            return HttpResponseRedirect('/assets/project_list/')
    else:
        pf = ProjectForm(instance=project_data)
    return render(request,'assets/project_edit.html', locals())

@permission_required('assets.Can_delete_project', login_url='/auth_error/')
def project_delete(request, uuid):
    project_data = Project.objects.get(pk=uuid)
    project_data.delete()
    return HttpResponseRedirect("/assets/project_list/")

##系统服务信息
@permission_required('assets.Can_add_Service', login_url='/auth_error/')
def service_add(request):
    lf = ServiceForm()
    if request.method == 'POST':
        lf = ServiceForm(request.POST)
        if lf.is_valid():
            result = lf.save(commit=False)
            result.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/service_add.html',locals())

@permission_required('assets.Can_delete_Service', login_url='/auth_error/')
def service_delete(request, uuid):
    service_data = Service.objects.get(pk=uuid)
    service_data.delete()
    return HttpResponseRedirect("/assets/service_list/")

@permission_required('assets.Can_add_Service', login_url='/auth_error/')
def service_list(request):
    data = Service.objects.all()
    return render(request,'assets/service_list.html',locals())

@permission_required('assets.Can_add_service', login_url='/auth_error/')
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