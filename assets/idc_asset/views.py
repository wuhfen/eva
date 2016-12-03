#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from .forms import IDCForm,CabinetForm,MoudleForm
from assets.models import IDC, Moudle, Cabinet

###机房信息
@permission_required('assets.Can_add_IDC', login_url='/auth_error/')
def idc_add(request):
	lf = IDCForm()
	if request.method == 'POST':
		lf = IDCForm(request.POST)
		if lf.is_valid():
			result = lf.save(commit=False)
			result.save()
			return HttpResponseRedirect('/allow/welcome/')
	return render(request,'assets/idc_add.html',locals())

@permission_required('assets.Can_delete_IDC', login_url='/auth_error/')
def idc_delete(request, uuid):
    idc_data = IDC.objects.get(pk=uuid)
    idc_data.delete()
    return HttpResponseRedirect("/assets/idc_list/")

@permission_required('assets.Can_add_IDC', login_url='/auth_error/')
def idc_list(request):
	data = IDC.objects.all()
	return render(request,'assets/idc_list.html',locals())

@permission_required('assets.Can_add_IDC', login_url='/auth_error/')
def idc_edit(request,uuid):
    idc_data = IDC.objects.get(pk=uuid)
    if request.method == 'POST':
        lf = IDCForm(request.POST, instance=idc_data)
        
        if lf.is_valid():
            result = lf.save()
            return HttpResponseRedirect('/assets/idc_list/')
    else:
        lf = IDCForm(instance=idc_data)
    return render(request,'assets/idc_edit.html', locals())

@permission_required('assets.Can_add_IDC', login_url='/auth_error/')
def idc_details(request,uuid):
    idc_data = IDC.objects.get(pk=uuid)
    idc_moudle = idc_data.moudle_set.all()
    NN = [n.name for n in idc_moudle]
    all_cabinet = Cabinet.objects.all()
    CN = [ c.model.name for c in all_cabinet]

    return render(request,'assets/idc_details.html',locals())

##机房区域信息
@permission_required('assets.Can_add_Moudle', login_url='/auth_error/')
def moudle_add(request):
    lf = MoudleForm()
    if request.method == 'POST':
        lf = MoudleForm(request.POST)
        if lf.is_valid():
            result = lf.save(commit=False)
            result.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/moudle_add.html',locals())

@permission_required('assets.Can_delete_Moudle', login_url='/auth_error/')
def moudle_delete(request, uuid):
    moudle_data = Moudle.objects.get(pk=uuid)
    moudle_data.delete()
    return HttpResponseRedirect("/assets/moudle_list/")

@permission_required('assets.Can_add_Moudle', login_url='/auth_error/')
def moudle_list(request):
    data = Moudle.objects.all()
    return render(request,'assets/moudle_list.html',locals())

@permission_required('assets.Can_add_Moudle', login_url='/auth_error/')
def moudle_edit(request,uuid):
    moudle_data = Moudle.objects.get(pk=uuid)
    if request.method == 'POST':
        lf = MoudleForm(request.POST, instance=moudle_data)
        
        if lf.is_valid():
            result = lf.save()
            return HttpResponseRedirect('/assets/moudle_list/')
    else:
        lf = MoudleForm(instance=moudle_data)
    return render(request,'assets/moudle_edit.html', locals())


##机柜区域
@permission_required('assets.Can_add_Cabinet', login_url='/auth_error/')
def cabinet_add(request):
    lf = CabinetForm()
    if request.method == 'POST':
        lf = CabinetForm(request.POST)
        if lf.is_valid():
            result = lf.save(commit=False)
            result.save()
            return HttpResponseRedirect('/allow/welcome/')
    return render(request,'assets/cabinet_add.html',locals())

@permission_required('assets.Can_delete_Cabinet', login_url='/auth_error/')
def cabinet_delete(request, uuid):
    cabinet_data = Cabinet.objects.get(pk=uuid)
    cabinet_data.delete()
    return HttpResponseRedirect("/assets/cabinet_list/")

@permission_required('assets.Can_add_Cabinet', login_url='/auth_error/')
def cabinet_list(request):
    data = Cabinet.objects.all()
    return render(request,'assets/cabinet_list.html',locals())

@permission_required('assets.Can_add_Cabinet', login_url='/auth_error/')
def cabinet_edit(request,uuid):
    cabinet_data = Cabinet.objects.get(pk=uuid)
    if request.method == 'POST':
        lf = CabinetForm(request.POST, instance=cabinet_data)
        
        if lf.is_valid():
            result = lf.save()
            return HttpResponseRedirect('/assets/cabinet_list/')
    else:
        lf = CabinetForm(instance=cabinet_data)
    return render(request,'assets/cabinet_edit.html', locals())