#!/usr/bin/env python
# coding:utf-8


from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
from automation.models import gengxin_code,gengxin_deploy
import time
from api.git_api import Repo
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
        self.git_web_export_dir = self.base_export_dir + siteid
        self.git_pub_pc_php_export_dir = self.base_export_dir + "public_pc_php/"
        self.git_pub_phone_php_export_dir = self.base_export_dir + "public_phone_php/"
        self.git_pub_pc_js_export_dir = self.base_export_dir + "public_pc_js/"
        self.git_pub_phone_js_export_dir = self.base_export_dir + "public_phone_js/"
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


    def web_export(self,reversion=None):
        giturl = "http://%s:%s@git.dtops.cc:web/%s.git"% (self.guser,self.gpass,self.siteid)
        print giturl
        repo = Repo()
