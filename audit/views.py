#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from .models import ops_command_log
from django.http import HttpResponseRedirect, HttpResponse
import json
from .forms import RecordOPSForm
from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.
@permission_required('assets.add_ops_command_log', login_url='/auth_error/')
def record_ops_command(request):
    log_obj = ops_command_log.objects.all()
    return render(request,'audit/record_ops_command.html',locals())

def record_command(request):
    if request.is_ajax():
        start = request.POST['start']
        end = request.POST['end']
        command = request.POST['commd']
        ops_command_log.objects.create(start_time = start,end_time=end,command=command,user=request.user)
        return HttpResponse("success")
    return HttpResponse("error")

@permission_required('assets.add_ops_command_log', login_url='/auth_error/')
def record_command_edit(request,uuid):
    log_obj = ops_command_log.objects.get(pk=uuid)
    rf = RecordOPSForm(instance=log_obj)
    if request.method == 'POST':
        rf = RecordOPSForm(request.POST,instance=log_obj)
        if rf.is_valid():
            rf.save()
    return render(request,'audit/record_command_edit.html',locals())
