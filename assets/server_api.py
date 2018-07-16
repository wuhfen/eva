# coding:utf-8
from assets.models import Server,Asset,NIC
from accounts.models import CustomUser as Users
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

#查询接口
#提交关键字,返回主机信息
#返回格式:{'result':True,'data':{'host':'','user':'','port':'','passwd':''}}
#请求格式:
#   method:POST
#   token: true
#   key: true
#   url:/server_info
#   curl -d "token=11111" url

def get_server_by_key(key):
    ssh_hosts = [i for i in Server.objects.filter(ssh_host__contains=key) if i]
    purpose = [asset.server for asset in Asset.objects.filter(purpose__contains=key) if asset]
    nic = [ip.asset.server for ip in NIC.objects.filter(ipaddress__contains=key) if ip]
    servers = ssh_hosts+purpose+nic
    if servers:
        servers = list(set(servers))
        return [{'host': i.ssh_host,'user':i.ssh_user,'port':i.ssh_port,'passwd':i.ssh_password,'purpose':i.asset.purpose} for i in servers]
    else:
        return False

@csrf_exempt
def get_server(request):
    token = "Hi!MyNameIsTokenBoy"
    if request.method == 'POST':
        req_token = request.POST.get('token')
        key = request.POST.get('key')
        if token == req_token:
            data = get_server_by_key(key)
            if data: return JsonResponse({'result':True,'data':data})
    return JsonResponse({'result':False,'data':{}},safe=False)


