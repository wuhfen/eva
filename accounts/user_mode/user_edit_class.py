#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.shortcuts import render_to_response, render
from django.contrib.auth.decorators import login_required
from accounts.forms import UserCreateForm, useredit_from
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib.auth.hashers import make_password

from django.views.decorators.csrf import csrf_protect
from accounts.models import *
import time,json
from django.contrib.auth.decorators import login_required
from cmdb_auth.views import check_auth


@login_required
@csrf_protect
def user_edit(request, id):
    status = check_auth(request, "edit_user")
    if not status:
        return render(request, 'default/error_auth.html', locals())

    data = CustomUser.objects.get(id=id)
    # data_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    if request.method == 'POST':
        # if request.POST.getlist("password1") == request.POST.getlist("password2"):
        uf = useredit_from(request.POST, instance=data)
        # print uf
        if uf.is_valid():
        	
            # zw = uf.save(commit=False)
            # zw.last_login = data_time
            # zw.date_joined = data_time
            # zw.username = data.username
            # zw.id = id
            uf.save()
            return HttpResponseRedirect("/accounts/user_list/")
    else:
        uf = useredit_from(instance=data)
    return render(request,'accounts/user_edit.html', locals())
