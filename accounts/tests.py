#!/usr/bin/python
# -*-coding:utf-8-*-
from django.test import TestCase
from django.http import HttpResponseRedirect, HttpResponse

def username_login(request):
	return HttpResponse("result:true data{code:xxxxxxx,message:success}")
    # if request.method == "POST":
    #     form = LoginForm(request.POST)
    #     login_errors = []
    #     if form.is_valid():
    #         username = request.POST.get('username', '')
    #         password = request.POST.get('password', '')
    #         data = CustomUser.objects.get(username=username)
    #         check_data = check_password(password, data.password)
    #         if check_data:
    #             data.backend = 'django.contrib.auth.backends.ModelBackend'
    #             login(request, data)
    #             auth_data = auth_class(request.user)
    #             request.session["fun_auth"] = auth_data
    #             user_data = CustomUser.objects.get(email=request.user)
    #             user_data.session_key = request.session.session_key
    #             user_data.save()
    #             request.session.set_expiry(28800)
    #             return HttpResponseRedirect('/index/')
    #         else:
    #             login_errors.append("用户或密码错误，请联系管理员！")
    # return render(request,'accounts/login.html',locals())
