#!/usr/bin/env python
# coding:utf-8
from django.http import HttpResponseRedirect, HttpResponse
from models import Platform

import json
import urllib

def get_platform_data(request):
    data = {}
    if request.GET.get('tag'):
        tag = request.GET.get('tag')
        print urllib.unquote(tag)

        plat_data = Platform.objects.get(name=urllib.unquote(tag))
        print tag
        data['fornt_station'] = {}
        data['fornt_station']['hosts'] = []
        data['fornt_station']['vars'] = {"ansible_ssh_user":"root"}
        data['_meta'] = {}
        data['_meta']['hostvars'] = {}
        for i in plat_data.front_station.all():
            data['fornt_station']['hosts'].append(i.ssh_host)
            data['_meta']['hostvars'][i.ssh_host] = {"ansible_ssh_port":i.ssh_port,"ansible_ssh_pass":i.ssh_password}

        return HttpResponse(json.dumps(data, ensure_ascii=True, indent=4, ))