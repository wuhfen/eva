#!/usr/bin/env python
# coding:utf-8
from .models import accelerated_server_manager
from api.ssh_api import run_ftp,run_cmd
import subprocess


def jiasu_conf_rsync(method="local",host=None,port=None,user=None,password=None):
    data = accelerated_server_manager.objects.filter(online=True)
    server_list=[ {i.name:i.host_master} for i in data]
    servers=""
    cmd='''pgrep lsyncd && pkill lsyncd && lsyncd -log Exec /etc/lsyncd.conf && lsyncd -log Exec /etc/jiasu_lsyncd.conf && echo "已重启lsyncd服务" || (lsyncd -log Exec /etc/lsyncd.conf && lsyncd -log Exec /etc/jiasu_lsyncd.conf)
    '''
    for i in data:
        servers=servers+'    "%s", -- %s\n'% (i.host_master,i.name)
    comment="""-- this file is sync from cmdb_server
settings {
    logfile ="/data/run/lsyncd.log",
    statusFile ="/data/run/lsyncd.status",
    inotifyMode = "CloseWrite",
    maxProcesses = 1,
    insist = true,
    }
servers = {
    -- "119.160.235.164"
%s
}
for _, server in ipairs(servers) do
sync {
    default.rsyncssh,
    source="/data/jiasu/nginx_conf/conf",
    host=server,
    targetdir="/usr/local/nginx/conf",
    maxDelays=5,
    delay=0,
    delete="running",
    exclude={ ".*", "*.tmp" },
    rsync = {
        binary="/usr/bin/rsync",
        archive = true,
        compress = true,
        verbose = true,
        }
    }
end
    """% servers
    with open('/etc/jiasu_lsyncd.conf','wb+') as f:
        f.write(comment)
    if method=="local":
        print "restart lsyncd service"
        p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        res = p.stdout.read()
        print res
    else:
        port=int(port)
        run_ftp(host,port,password,user,'/etc/jiasu_lsyncd.conf','/etc/jiasu_lsyncd.conf')
        run_cmd(host,port,password,user,cmd)