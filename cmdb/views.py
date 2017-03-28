from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from assets.forms import RAMForm,AssetForm,NICForm
from assets.models import Asset, NIC
from django.contrib.auth.decorators import login_required
import time
from assets.system_opt.init_system import init_sys

# Create your views here.
@login_required()
def index(request):
    return render(request,'default/index.html',locals())

def auth_error(request):
    return render(request,'default/error_auth.html',locals())

def success(request):
    return render(request,'default/success.html',locals())

def test(request):
    init = init_sys('18')
    print "hello"
    data = "Hello World"
    return render(request,'default/test233.html',locals())
