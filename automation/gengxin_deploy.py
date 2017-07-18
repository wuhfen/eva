#!/usr/bin/env python
# coding:utf-8


from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
from automation.models import gengxin_code,gengxin_deploy
import time
from api.svn_api import Svnrepo
import subprocess
from api.ssh_api import ssh_cmd
from assets.models import Server
from api.ansible_api import MyTask, MyPlayTask

class website_deploy(object):
    def __init__(self,env,siteid,method="gengxin"):
        self.base_export_dir = "/data/webserver/" + env + "/export/"
        self.base_merge_dir = "/data/webserver/"+ env + "/merge/"
        self.web_export_dir = self.base_export_dir +"Web/"+ siteid
        self.pub_export_dir = self.base_export_dir +"Pub/"+ siteid
        self.conf_export_dir = self.base_export_dir +"Conf/"+ siteid
        self.now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.method = method
        self.env = env
        self.siteid = siteid
        self.pc_merge_dir = self.base_merge_dir + siteid.replace('m','')
        self.phone_merge_dir = self.pc_merge_dir + "/m"
        if self.method == "fabu":
            self.web_export()
            self.pub_export()
            self.conf_export()

    def last_release(self,classify,isphone=None):
        web_url = "svn://47.91.176.204/"+ self.siteid
        if "f" in self.siteid:
            web_phone_url = "svn://47.91.176.204/"+ self.siteid.replace('f','mf')
        else:
            web_phone_url = "svn://47.91.176.204/"+ self.siteid + "m"
        pub_pc_url = "svn://119.9.91.21/1000m_public"
        pub_phone_url = "svn://119.9.91.21/1000_public"

        if classify == "web":
            print "web_start"
            repo = Svnrepo(self.web_export_dir, "yunwei", "4OTk2ZmI5M")
            pubrepo = Svnrepo(self.pub_export_dir, "yunwei", "tYbmhKpcv2")
            web_reversion = repo.svn_last_reversion(web_url)
            pub_pc_reversion = pubrepo.svn_last_reversion(pub_pc_url)
            if isphone:
                web_phone_reversion = repo.svn_last_reversion(web_phone_url)
                pub_phone_reversion = pubrepo.svn_last_reversion(pub_phone_url)
                return "web最新版本："+web_reversion+" public最新版本："+pub_pc_reversion+" 手机web最新版本："+web_phone_reversion+" 手机public最新版本："+pub_phone_reversion
            return "web最新版本："+web_reversion+" public最新版本："+pub_pc_reversion
        elif classify == "pa":
            print "pa_start"
            pubrepo = Svnrepo("/data", "yunwei", "tYbmhKpcv2")
            pub_pc_reversion = pubrepo.svn_last_reversion(pub_pc_url)
            return "public最新版本："+pub_pc_reversion
        else:
            print "pam_statr"
            pubrepo = Svnrepo("/data", "yunwei", "tYbmhKpcv2")
            pub_phone_reversion = pubrepo.svn_last_reversion(pub_phone_url)
            return "手机public最新版本："+pub_phone_reversion



    def web_export(self,reversion=None):
        svnurl = "svn://47.91.176.204/"+ self.siteid
        svn_user = "yunwei"
        svn_pass = "4OTk2ZmI5M"
        repo = Svnrepo(self.web_export_dir, svn_user, svn_pass)
        if reversion:
            res = repo.svn_update(reversion)
        else:
            genxin_code_dir(self.web_export_dir)
            res = repo.svn_checkout(svnurl,ccdir=self.web_export_dir)


    def pub_export(self,reversion=None):
        if "m" in self.siteid:
            svnurl = "svn://119.9.91.21/1000m_public"
        else:
            svnurl = "svn://119.9.91.21/1000_public"
        svn_user = "yunwei"
        svn_pass = "tYbmhKpcv2"
        repo = Svnrepo(self.pub_export_dir, svn_user, svn_pass)
        if reversion:
            res = repo.svn_update(reversion)
        else:
            genxin_code_dir(self.pub_export_dir)
            res = repo.svn_checkout(svnurl,ccdir=self.pub_export_dir)

    def conf_export(self,reversion=None):
        if self.env == "huidu":
            svnurl = "svn://119.9.91.21/huidu_config/"+ self.siteid+"_config"
        else:
            svnurl = "svn://119.9.91.21/1000_config/" + self.siteid + "_config"
        svn_user = "yunwei"
        svn_pass = "tYbmhKpcv2"
        repo = Svnrepo(self.conf_export_dir, svn_user, svn_pass)
        if reversion:
            res = repo.svn_update(reversion)
        else:
            genxin_code_dir(self.conf_export_dir)
            res = repo.svn_checkout(svnurl,ccdir=self.conf_export_dir)

    def merge_web(self,uuid):
        data = gengxin_code.objects.get(pk=uuid)
        genxin_code_dir(self.pc_merge_dir)  #清空或创建目录
        if "m" in self.siteid:
            pc_web_dir = self.base_export_dir + "Web/" + self.siteid.replace('m','')
            pc_pub_dir = self.base_export_dir + "Pub/" + self.siteid.replace('m','')
            pc_conf_dir = self.base_export_dir + "Conf/" + self.siteid.replace('m','')
            phone_web_dir = self.web_export_dir
            phone_pub_dir = self.pub_export_dir
            phone_conf_dir = self.conf_export_dir
        else:
            pc_web_dir = self.web_export_dir
            pc_pub_dir = self.pub_export_dir
            pc_conf_dir = self.conf_export_dir
            if "f" in self.siteid:
                phone_web_dir = self.base_export_dir + "Web/" + self.siteid.replace('f','mf')
                phone_pub_dir = self.base_export_dir + "Pub/" + self.siteid.replace('f','mf')
                phone_conf_dir = self.base_export_dir + "Conf/" + self.siteid.replace('f','mf')
            else:
                phone_web_dir = self.web_export_dir + 'm'
                phone_pub_dir = self.pub_export_dir + 'm'
                phone_conf_dir = self.conf_export_dir + 'm'

        if data.phone_site:
            print "合并pc and 手机站"
            cmd = '''\cp -ar %s/*  %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/php/ && echo "PC端已合并" && \cp -ar %s/m %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/php/ && echo "phone端已合并,合并完成"
            '''% (pc_web_dir,self.pc_merge_dir,pc_pub_dir,self.pc_merge_dir,pc_conf_dir,self.pc_merge_dir,phone_web_dir,self.pc_merge_dir,phone_pub_dir,self.phone_merge_dir,phone_conf_dir,self.phone_merge_dir)
        else:
            print "只有合并pc站"
            cmd = '''\cp -ar %s/*  %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/php/ && echo "PC端已合并" && echo "无phone端,合并完成"
            '''% (pc_web_dir,self.pc_merge_dir,pc_pub_dir,self.pc_merge_dir,pc_conf_dir,self.pc_merge_dir)
        print cmd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        res = p.stdout.readlines()
        print res
        return res

    def ansible_rsync_web(self,remoteips,rsync_command,last_command,excludes):
        remotedir = "/data/wwwroot/"+self.siteid.replace('m','')
        exclude = genxin_exclude_file(excludes)
        for i in remoteips.split('\r\n'):
            print "i="+i
            rsync_command_res = ssh_cmd(i,rsync_command)  #执行推送代码前命令
            obj = Server.objects.get(ssh_host=i)
            task = MyTask(gen_resource(obj))
            rsync_res = task.genxin_rsync(self.pc_merge_dir,remotedir,exclude) #将代码从CMDB本地目录推送到服务器目录，需要此机器可以公钥访问源站
            last_command_res = ssh_cmd(i,last_command)  #执行代码推送后命令

    def web_front_domain(self,domains,remoteips,classify,isphone=None):
        server_names = domains.replace('\r\n'," ")
        if classify == "front":
            remote_dir = "/usr/local/nginx/conf/vhost/"
            remote_nginx_file = self.siteid+".conf"
            siteid = self.siteid.replace('f','')
            if "f" in self.siteid:
                if isphone:
                    local_nginx_file = "front_fu.conf"
                else:
                    local_nginx_file = "front_fu_phone.conf"
            else:
                if isphone == True:
                    local_nginx_file = "front_zhu.conf"
                else:
                    local_nginx_file = "front_zhu_phone.conf"
            print local_nginx_file
            resource = gen_resource([Server.objects.get(ssh_host=i) for i in remoteips.split('\r\n')])
        elif classify == "agent":
            remote_dir = "/usr/local/nginx/conf/vhost/"
            if self.env == "huidu":
                remote_nginx_file = self.siteid+"_huidu.conf"
            else:
                remote_nginx_file = self.siteid+".conf"
            siteid = self.siteid.replace('f','')
            local_nginx_file = "agent.conf"
            resource = gen_resource(Server.objects.get(ssh_host='10.10.240.20'))
            # resource = gen_resource(Server.objects.get(ssh_host='47.89.30.192'))
        else:
            remote_dir = "/usr/local/nginx/conf/vhost/"
            remote_nginx_file = self.siteid+".conf"
            siteid = self.siteid.replace('f','')
            local_nginx_file = "backend.conf"
            # resource = gen_resource([Server.objects.get(ssh_host=i) for i in ['119.9.93.246','47.90.44.247']])
            resource = gen_resource([Server.objects.get(ssh_host=i) for i in ['10.10.1.115']])
        playtask = MyPlayTask(resource)
        playtask.rsync_nginx_conf(local_nginx_file,remote_dir,remote_nginx_file,siteid,server_names)


