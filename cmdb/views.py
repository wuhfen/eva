from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from assets.forms import RAMForm,AssetForm,NICForm
from assets.models import Asset, NIC
import time

# Create your views here.
def index(request):
    return render(request,'default/index.html',locals())

def auth_error(request):
    return render(request,'default/error_auth.html',locals())

def success(request):
    return render(request,'default/success.html',locals())

def test(request):
    if request.method == 'POST':
        rr = request.POST.get('checkbox1','')
        return HttpResponse(rr)
    return render(request,'default/test233.html',locals())

def navtest(request):
    return render(request,'default/test233.html',locals())