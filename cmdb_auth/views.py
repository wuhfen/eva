#!/usr/bin/python
# -*-coding:utf-8-*-

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sessions.backends.db import SessionStore
import json
import hashlib, time
from cmdb.settings import auth_key

from cmdb_auth.models import auth_group, user_auth_cmdb
from .forms import cmdb_groupForm, group_auth_addForm, auth_group_userForm
from accounts.models import CustomUser
from accounts.auth_session import auth_class
# Create your views here.

def check_auth(request, data):
    if request.user.is_superuser or request.session["fun_auth"].get(data, False):
        return True
    else:
        return False

def auth_session_class(uuid):
    u"""当权限组被禁用的时候调用此函数，重置当前用户权限"""
    data_id = auth_group.objects.get(uuid=uuid)
    all_user = data_id.group_user.all()
    for i in all_user:
        if i.session_key:
            s = SessionStore(session_key=i.session_key)
            s["fun_auth"] = auth_class(i)
            s.save()

    return True


@login_required
def group_add(request):
    u"""创建权限组"""
    data = cmdb_groupForm()
    if request.method == 'POST':
        uf = cmdb_groupForm(request.POST)
        if uf.is_valid():
            uf.save()
            return HttpResponseRedirect("/auth/cmdb_auth_index/")
        return render(request,'cmdb_auth/group_add.html', locals())
    return render(request,'cmdb_auth/group_add.html', locals())

@login_required
def group_edit(request, uuid):
    u"""修改权限组"""
    uuid = str(uuid)
    group_uuid = auth_group.objects.get(uuid=uuid)
    if request.method == 'POST':
        uf = cmdb_groupForm(request.POST, instance=group_uuid)
        if uf.is_valid():
            uf.save()
            return HttpResponseRedirect("/success/")

    else:
        data = cmdb_groupForm(instance=group_uuid)

    return render(request,'cmdb_auth/group_edit.html', locals())

@login_required
def group_status(request, uuid):
    u"""修改组状态是否禁用"""
    uuid = str(uuid)
    group_uuid = auth_group.objects.get(uuid=uuid)
    if group_uuid.enable:
        group_uuid.enable = False
        group_uuid.save()
        auth_session_class(uuid)
    else:
        group_uuid.enable = True
        group_uuid.save()
        auth_session_class(uuid)

    return HttpResponse(json.dumps({"status": 200, "msg": "ok"}, ensure_ascii=False, indent=4, ))

@login_required
def group_delete(request, uuid):
    u"""删除权限组"""
    uuid = str(uuid)
    group_uuid = auth_group.objects.get(uuid=uuid)
    group_uuid.group_user.clear()
    group_uuid.delete()

    return HttpResponseRedirect("/auth/cmdb_auth_index/")

@login_required
def group_add_auth(request, uuid):
    u"""给组赋予权限"""
    uuid = str(uuid)
    group_uuid = auth_group.objects.get(uuid=uuid)
    try:
        group_data = user_auth_cmdb.objects.get(group_name=uuid)
        data = group_auth_addForm(instance=group_data)
    except:
        data = group_auth_addForm()
    if request.method == 'POST':
    	try:
    		uf = group_auth_addForm(request.POST, instance=group_data)
    	except:
    		uf = group_auth_addForm(request.POST)

	if uf.is_valid():
	    uf.save()
	    auth_session_class(uuid)

    return render(request,'cmdb_auth/group_add_auth.html', locals())

def cmdb_group_user(request, uuid):
    u"""权限组添加用户"""
    uuid = str(uuid)
    data_id = auth_group.objects.get(uuid=uuid)

    if request.method == 'POST':
        uf = auth_group_userForm(request.POST, instance=data_id)
        if uf.is_valid():
            uf.save()
            auth_session_class(uuid)

    data = auth_group_userForm(instance=data_id)
    userall = CustomUser.objects.all()
    all_user = data_id.group_user.all()

    user_list = [x.first_name for x in all_user]

    return render(request,'cmdb_auth/group_user.html', locals())

@login_required
def auth_index(request):
    u"""
    权限分配首页
    :param request:
    :return:
    """
    data = auth_group.objects.all().order_by("-date_time")
    group_user_count = {}

    for i in data:
        data_id = auth_group.objects.get(uuid=i.uuid)
        group_user_count[i.uuid] = data_id.group_user.all().count()

    return render(request,'cmdb_auth/index.html', locals())

