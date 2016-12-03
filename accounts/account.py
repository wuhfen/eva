#!/usr/bin/python
#-*-coding:utf-8-*-
from django.template import RequestContext
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from forms import LoginForm, ChangePasswordForm

from models import CustomUser as User
from accounts.auth_session import auth_class
from django.contrib.auth.hashers import make_password, check_password

import hashlib
import time
from cmdb.settings import auth_key
from .forms import NewPasswordForm, ResetPasswordForm
from django.core.mail import send_mail
from validators import Checkpasswd

# Create your views here.
def user_login(request):
    if request.method == 'GET':  
        form = LoginForm()  
        return render(request,'accounts/login.html',locals())
    else:
        form = LoginForm(request.POST)
        login_errors = []
        if form.is_valid():
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active: 
                login(request, user)
                auth_data = auth_class(request.user)
                request.session["fun_auth"] = auth_data
                user_data = User.objects.get(username=request.user)
                user_data.session_key = request.session.session_key
                user_data.save()
                request.session.set_expiry(28800)
                return HttpResponseRedirect('/index/')
            else:
                login_errors.append("用户或密码错误，请联系管理员！")
                return render(request,'accounts/login.html',locals())
        else:
            return render(request,'accounts/login.html',locals())


def user_logout(request):
    u"""
    退出登录
    """
    logout(request)
    # request.session.flush()
    return HttpResponseRedirect("/accounts/login/")

def new_password(request):
    u"""新注册用户填写密码邮件"""
    uuid = request.GET.get("uuid", False)
    token = request.GET.get('token', False)

    # try:
    data = User.objects.get(uuid=uuid)
    new_token = str(hashlib.sha1(data.username + auth_key + data.uuid +
                                     time.strftime('%Y-%m-%d', time.localtime(time.time()))).hexdigest())
    uf = NewPasswordForm()
    if token == new_token:
        if request.method == 'POST':
            uf = NewPasswordForm(request.POST, instance=data)
            if uf.is_valid():
                rst = Checkpasswd(request.POST.get("newpassword"))
                if rst:
                    password = request.POST.get("newpassword")
                    zw = uf.save(commit=False)
                    zw.password = make_password(password, None, 'pbkdf2_sha256')
                    zw.save()
                    status = True
                    return HttpResponseRedirect('/')
                else:
                    status = False
        status = True
        return render(request,'accounts/new_password.html', locals())
    # except:
    #     print "error"
    #     pass
    return render(request,'default/404.html', locals())

@csrf_exempt
def forgetpasswd(request):
    u"""找回忘记的密码通过邮件"""
    uf = ResetPasswordForm()
    if request.method == "POST":
        email = request.POST.get("email", False)
        if email:
            try:
                new_user = User.objects.get(email=email)
                token = str(hashlib.sha1(new_user.username + auth_key + new_user.uuid + time.strftime('%Y-%m-%d', time.localtime(time.time()))).hexdigest())
                url = u'http://%s/accounts/newpasswd/?uuid=%s&token=%s' % (request.get_host(), new_user.uuid, token)
                mail_title = u'运维自动化找回密码'
                mail_msg = u"""
                Hi,%s:
                    请点击以下链接修改密码,此链接当天有效:
                        %s
                    有任何问题，请随时和运维组联系。
                """ % (new_user.first_name, url)

                send_mail(mail_title, mail_msg, u'运维自动化<devops@funshion.net>', [new_user.email], fail_silently=False)

                return HttpResponseRedirect("/accounts/login/")
            except:
                pass
        return render(request,'default/404.html', locals())
    return render(request,'accounts/forget_password.html', locals())

