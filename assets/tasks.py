from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task

from api.common_api import gen_resource
from api.ansible_api import MyPlayTask
from .models import Server,Asset,NIC
from api.zabbix_api import zabbixtools

@shared_task()
def init_sys(dataid):
    current_task.update_state(state="PROGRESS")
    data = Server.objects.get(uuid=dataid)
    resource = gen_resource(data)
    ansible_playtask = MyPlayTask(resource)
    ansible_playtask.initialization_system()
    Server.objects.filter(pk=dataid).update(ssh_port='22992')
    zai = zabbixtools("http://47.90.33.131:8090/","user","password")
    zai.host_create(data.ssh_host,data.ssh_host,"10050","Linux servers")
    return "123456789"

@shared_task()
def batch_add_virtual(content_list):
    current_task.update_state(state="PROGRESS")
    host_list = [x.ssh_host for x in Server.objects.all()]
    for i in content_list:
        j = i.split()
        if j[0].split(',')[0] not in host_list:
            if len(j) > 4:
                adata = Asset(asset_type='virtual',purpose=j[4])
                adata.save()
                if "," not in j[0]:
                    vdata = Server(asset=adata,ssh_host=j[0],ssh_port=j[1],ssh_user=j[2],ssh_password=j[3])
                    vdata.save()
                else:
                    ips = j[0].split(',')
                    vdata = Server(asset=adata,ssh_host=ips[0],ssh_port=j[1],ssh_user=j[2],ssh_password=j[3])
                    vdata.save()
                    del ips[0]
                    for s in ips:
                        ndata = NIC(asset=adata,ipaddress=s,netmask="255.255.255.0",name="eth1")
                        ndata.save()
            elif len(j) == 3:
                adata = Asset(asset_type='virtual',purpose="nothing")
                adata.save()
                if "," not in j[0]:
                    vdata = Server(asset=adata,ssh_host=j[0],ssh_port=j[1],ssh_user=j[2],ssh_password=j[3])
                    vdata.save()
                else:
                    ips = j[0].split(',')
                    vdata = Server(asset=adata,ssh_host=ips[0],ssh_port=j[1],ssh_user=j[2],ssh_password=j[3])
                    vdata.save()
                    del ips[0]
                    for s in ips:
                        ndata = NIC(asset=adata,ipaddress=s,netmask="255.255.255.0",name="eth1")
                        ndata.save()
            else:
                adata = Asset(asset_type='virtual',purpose="nothing")
                adata.save()
                if "," not in j[0]:
                    vdata = Server(asset=adata,ssh_host=j[0],ssh_port="22992",ssh_user="root",ssh_password="nothing")
                    vdata.save()
                else:
                    ips = j[0].split(',')
                    vdata = Server(asset=adata,ssh_host=ips[0],ssh_port="22992",ssh_user="root",ssh_password="nothing")
                    vdata.save()
                    del ips[0]
                    for s in ips:
                        ndata = NIC(asset=adata,ipaddress=s,netmask="255.255.255.0",name="eth1")
                        ndata.save()
    return "batch_add_virtual_success"




