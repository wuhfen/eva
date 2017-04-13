from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task

from api.common_api import gen_resource
from api.ansible_api import MyPlayTask
from .models import Server
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