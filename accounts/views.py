#!/usr/bin/python
# -*-coding:utf-8-*-

from django.shortcuts import render_to_response, render
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from cmdb_auth.views import check_auth
from models import common_uuid, CustomUser
from .forms import UserCreateForm, department_from
import hashlib
import time
from django.core.mail import send_mail
from cmdb.settings import auth_key, EMAIL_PUSH

from models import department_Mode

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def register(request):
# u"""
# 注册用户
# """
    # status = check_auth(request, "add_user")
    # if not status:
    #     return render(request,'default/error_auth.html', locals())

    content = {}
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.is_staff = 1
            new_user = form.save(commit=False)

            new_user.is_staff = 1
            new_user.session_key = ""
            new_user.uuid = common_uuid()
            new_user.save()
            if EMAIL_PUSH:
                token = str(hashlib.sha1(new_user.username + auth_key + new_user.uuid + time.strftime('%Y-%m-%d', time.localtime(time.time()))).hexdigest())
                #
                url = u'http://%s/accounts/newpasswd/?uuid=%s&token=%s' % (request.get_host(), new_user.uuid, token)
                mail_title = u'运维自动化初始密码'
                mail_msg = u"""
                Hi,%s:
                    请点击以下链接初始化运维自动化密码,此链接当天有效:
                        %s
                    有任何问题，请随时和运维组联系。
                """ % (new_user.first_name, url)
                #

                send_mail(mail_title, mail_msg, u'运维自动化<devops@ds.com>', [new_user.email], fail_silently=False)

            return HttpResponseRedirect("/accounts/user_list/")
        else:
            data = UserCreateForm()

            return render(request,'accounts/register.html', locals())
    else:
        data = UserCreateForm()
    return render(request,'accounts/register.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def user_select(request):
    u"""查看用户列表"""
    status = check_auth(request, "add_user")
    if not status:
	return render(request,'default/error_auth.html', locals())
    else:
	uf = CustomUser.objects.all().filter(is_active=True, is_staff=True)
    return render(request,'accounts/user_list.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def user_old(request):
    u"""
    离职用户列表
    """
    status = check_auth(request, "add_user")
    if not status:
        return render_to_response(request,'default/error_auth.html', locals())

    uf = CustomUser.objects.all().filter(is_active=False, is_staff=False)

    return render(request, 'accounts/user_list.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def user_forbidden(request):
    u"""
    禁用账户列表
    """
    status = check_auth(request, "add_user")
    if not status:
        return render(request,'default/error_auth.html', locals())

    uf = CustomUser.objects.all().filter(is_active=True, is_staff=False)

    return render(request, 'accounts/user_list.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def user_status(request, id):
    u"""
    禁用用户
    """
    status = check_auth(request, "delete_user")
    if not status:
        return render(request,'default/error_auth.html', locals())

    user = CustomUser.objects.get(pk=id)
    if user.is_staff:
        user.is_staff = False
    else:
        user.is_staff = True
    user.save()
    return render(request,'accounts/user_list.html', locals())


@permission_required('accounts.add_customuser', login_url='/auth_error/')
def user_delete(request, id):
    u"""
    删除用户
    """
    # status = check_auth(request, "delete_user")
    # if not status:
    #     return render_to_response('default/error_auth.html', locals())

    user = CustomUser.objects.get(pk=id)
    user.is_staff = False
    user.is_active = False
    user.save()

    return render(request,'accounts/user_list.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def department_list(request):
    u"""
    查看部门
    """
    status = check_auth(request, "add_department")
    if not status:
        return render(request,'default/error_auth.html', locals())

    uf = department_Mode.objects.all()

    content = {}

    for i in uf:
        user_list = []
        dep_all = i.users.all().values("first_name")

        for t in dep_all:
            user_list.append(t.get("first_name"))
        content[i.department_name] = {"user_list": user_list, "department_id": i.id}

    return render(request,'accounts/department_list.html', locals())

@permission_required('accounts.add_customuser', login_url='/auth_error/')
def department_view(request):
    u"""
    添加部门
    """
    status = check_auth(request, "add_department")
    if not status:
        return render_to_response('default/error_auth.html', locals())

    #验证post方法
    if request.method == 'POST':
        uf = department_from(request.POST)

        if uf.is_valid():
            uf.save()
        # return render_to_response('user/department_add.html', locals(), context_instance=RequestContext(request))
        return HttpResponseRedirect("/accounts/list_department/")
    else:
        uf = department_from()
    return render(request,'accounts/add_department.html', locals())


@permission_required('accounts.add_customuser', login_url='/auth_error/')
def department_edit(request, id):
    u"""
    部门修改
    """
    status = check_auth(request, "add_department")
    if not status:
        return render_to_response('default/error_auth.html', locals())

    data = department_Mode.objects.get(id=id)
    if request.method == 'POST':
        uf = department_from(request.POST, instance=data)
        u"验证数据有效性"
        if uf.is_valid():
            uf.save()
        return HttpResponseRedirect("/accounts/list_department/")

    uf = department_from(instance=data)
    return render(request,'accounts/edit_department.html', locals())