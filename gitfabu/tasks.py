#!/usr/bin/env python
# coding:utf-8

"""代码发布的复核，不影响审核的功能，在task发布任务结束后再次发送一个复核任务给工程，工程复核不走审核流程，
复核没有否定操作，只有复核完毕操作，复核完毕，发布任务中的isops状态设置为true，只有isops为true的时候才能在更新代码中看到此siteid，
任务详情页添加复核情况，复核在日志下方，只有发布才有复核，更新没有。
"""

from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task

from api.git_api import Repo
from api.ssh_api import ssh_cmd,ssh_check
from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
from gitfabu.audit_api import task_distributing,change_version_old_to_new
import time
import os
import re
from time import sleep
import subprocess
from assets.models import Server
from api.ansible_api import MyTask, MyPlayTask
from gitfabu.models import git_deploy,my_request_task,git_coderepo,git_ops_configuration,git_deploy_logs,git_code_update,git_deploy_audit
from business.models import DomainName,Business


@shared_task()
def send_message_task(tid,aid):
    task_distributing(tid,aid)
    return "All Message have been send"


class git_moneyweb_deploy(object):
    """现金网git调用类"""
    def __init__(self,uuid,method="gengxin"):
        data = git_deploy.objects.get(id=uuid)
        self.env = data.classify
        self.platform = data.platform
        self.siteid = data.name
        self.islock = data.islock
        self.usepub = data.usepub
        self.uuid = uuid
        self.now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.method = method
        self.results = []
        try:
            if self.platform == "现金网" or self.platform == "蛮牛":
                server_data = git_ops_configuration.objects.get(platform=data.platform,classify=data.classify,name="源站")
            elif self.platform == "VUE蛮牛":
                server_data = git_ops_configuration.objects.get(platform="蛮牛",classify=data.classify,name="源站")
            else:
                server_data = git_ops_configuration.objects.get(platform=data.platform,classify=data.classify,name=data.name)
            self.remoteip = server_data.remoteip
            self.remotedir = server_data.remotedir
            self.owner = server_data.owner
            self.exclude = server_data.exclude
            self.rsync_command = server_data.rsync_command
            self.last_command = server_data.last_command
        except:
            self.results.append("没有找到%s-%s-%s的源站配置,停止发布！"% (data.platform,data.classify,data.name))
            print "没有找到%s-%s-%s的源站配置,停止发布！"% (data.platform,data.classify,data.name)
            return None

        if self.env == "huidu":
            self.env_ch = "灰度"
        elif self.env == "online":
            self.env_ch = "生产"
        else:
            self.env_ch = "测试"

        if self.platform == "现金网":
            self.base_export_dir = "/data/moneyweb/" + self.env + "/export/"
            self.merge_dir = "/data/moneyweb/" + self.env + "/merge/" + self.siteid
            self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址
            self.php_pc_dir = self.base_export_dir + self.siteid + "_php_pc" #公共php代码pc端检出地址
            self.php_mobile_dir = self.base_export_dir + self.siteid + "_php_mobile" #公共php代码手机端检出地址
            self.js_pc_dir = self.base_export_dir + self.siteid + "_js_pc" #公共js代码pc端检出地址
            self.js_mobile_dir = self.base_export_dir + self.siteid + "_js_mobile" #公共js代码手机端检出地址
            self.config_dir = self.base_export_dir + "Config_" + self.siteid #公共config
        elif self.platform == "蛮牛":
            self.base_export_dir = "/data/manniuweb/" + self.env + "/export/"
            self.merge_dir = "/data/manniuvue/" + self.env + "/merge/" + self.siteid
            self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址
            self.php_dir = self.base_export_dir + self.siteid + "_mn_php" #公共php代码pc端检出地址
            self.js_dir = self.base_export_dir + self.siteid + "_mn_js" #公共js代码pc端检出地址
            self.config_dir = self.base_export_dir + self.siteid + "_mn_config" #公共config
        elif self.platform == "VUE蛮牛":
            self.base_export_dir = "/data/manniuvue/" + self.env + "/export/"
            self.merge_dir = "/data/manniuvue/" + self.env + "/merge/" + self.siteid
            self.pc_dir = self.base_export_dir + self.siteid+"_pc"  #私有仓库检出地址
            self.wap_dir = self.base_export_dir + self.siteid+"_wap"  #私有仓库检出地址
            self.php_dir = self.base_export_dir + self.siteid + "_mn_php" #公共php代码pc端检出地址
            self.config_dir = self.base_export_dir + self.siteid + "_mn_config" #公共config
        elif self.platform == "单个项目":
            self.base_export_dir = "/data/onlyproject/" + self.env + "/export/"
            self.merge_dir = "/data/onlyproject/" + self.env + "/merge/" + self.siteid
            self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址
        elif self.platform == "JAVA项目":
            self.base_export_dir = "/data/javaproject/" + self.env + "/export/"
            self.merge_dir = "/data/javaproject/" + self.env + "/merge/" + self.siteid
            self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址

        if self.method == "money_fabu":
            if not self.env == "test":
                ggsimida = self.export_config(branch="master")
            else:
                ggsimida = "yes"
            if ggsimida: b = self.export_git(what='php_pc')
            if b: c = self.export_git(what='js_pc')
            if c: d = self.export_git(what='php_mobile')
            if d: e = self.export_git(what='js_mobile')
            if e:
                self.update_release()
                self.merge_git()
                self.ansible_rsync_web()
                if data.conf_domain:
                    self.web_front_domain()
        elif self.method == "manniu_fabu":
            print "发布蛮牛web项目"
            self.export_git(what='web')
            self.export_git(what='js')
            self.export_git(what='php')
            self.export_git(what='config')
            self.update_release()
            self.merge_git()
            self.ansible_rsync_web()
            if data.conf_domain:
                self.web_front_domain()
        elif self.method == "vue_manniu_fabu":
            print "发布VUE蛮牛项目"
            a = self.export_git(what='vue_pc')
            if a: b = self.export_git(what='vue_wap')
            if b: c = self.export_git(what='vue_php')
            if c: d = self.export_git(what='vue_config')
            if d:
                self.update_release()
                self.merge_git()
                self.ansible_rsync_web()
                if data.conf_domain:
                    self.web_front_domain()
        elif self.method == "op_fabu":
            self.export_git(what='only')
            self.update_release()
            self.merge_git()
            self.ansible_rsync_web()
            if data.conf_domain: self.web_front_domain()
        elif self.method == "java_fabu":
            self.export_git(what='java')
            self.update_release()
            self.merge_git()
            self.ansible_rsync_web()
            if data.conf_domain: self.web_front_domain()

    def deploy_all_branch(self,what='web'):
        if what == 'php_pc':
            repo = Repo(self.base_export_dir+"php_pc/")
        elif what == 'php_mobile':
            repo = Repo(self.base_export_dir+ "php_mobile/")
        elif what == 'js_pc':
            repo = Repo(self.js_pc_dir)
        elif what == 'js_mobile':
            repo = Repo(self.js_mobile_dir)
        elif what == 'php':
            repo = Repo(self.base_export_dir+ "mn_php/")
        elif what == 'js':
            repo = Repo(self.base_export_dir+ "mn_js/")
        elif what == 'config':
            repo = Repo(self.base_export_dir+ "mn_config/")
        elif what == 'vue_pc':
            repo = Repo(self.pc_dir)
        elif what == 'vue_wap':
            repo = Repo(self.wap_dir)
        elif what == 'vue_php':
            repo = Repo(self.php_dir)
        elif what == 'vue_config':
            repo = Repo(self.config_dir)
        else:
            repo = Repo(self.web_dir)
        repo.git_checkout("master")
        repo.git_pull()
        return repo.git_all_branch()

    def branch_checkout(self,what='web',branch=None):
        if what == 'php_pc':
            repo = Repo(self.base_export_dir+"php_pc/")
        elif what == 'php_mobile':
            repo = Repo(self.base_export_dir+ "php_mobile/")
        elif what == 'js_pc':
            repo = Repo(self.js_pc_dir)
        elif what == 'js_mobile':
            repo = Repo(self.js_mobile_dir)
        elif what == 'php':
            repo = Repo(self.base_export_dir+ "mn_php/")
        elif what == 'js':
            repo = Repo(self.base_export_dir+ "mn_js/")
        elif what == 'config':
            repo = Repo(self.base_export_dir+ "mn_config/")
        elif what == 'vue_pc':
            repo = Repo(self.pc_dir)
        elif what == 'vue_wap':
            repo = Repo(self.wap_dir)
        elif what == 'vue_php':
            repo = Repo(self.php_dir)
        elif what == 'vue_config':
            repo = Repo(self.config_dir)
        else:
            repo = Repo(self.web_dir)
        if branch:
            repo.git_checkout(branch)
            repo.git_pull()
        else:
            repo.git_checkout("master")
        return repo.show_commit()


    def export_config(self,branch="master"):  #现金网配置文件灰度与线上公用，测试环境不需要检出配置文件
        url = "http://fabu:DSyunweibu110110@git.dtops.cc/config/"+ self.siteid +".git"
        genxin_code_dir(self.config_dir)
        repo = Repo(self.config_dir)
        try:
            res = repo.git_clone(url,self.config_dir)
            self.results.append("检出%s配置文件"% self.siteid)
        except:
            self.results.append("检出%s配置文件出错,没有该项目地址"% self.siteid)
            return None
        return self.results

    def export_git(self,what='web',branch="master",reversion=None):
        if what == 'php_pc' or what == 'php_mobile' or what == 'js_pc' or what == 'js_mobile':
            if what == 'php_pc': clone_dir=self.php_pc_dir
            if what == 'php_mobile': clone_dir=self.php_mobile_dir
            if what == 'js_pc': clone_dir=self.js_pc_dir
            if what == 'js_mobile': clone_dir=self.js_mobile_dir
            try:
                data = git_coderepo.objects.get(platform=self.platform,classify=self.env,title=what,ispublic=True)
                auth = "//"+data.user+":"+data.passwd+"@"
                self.repo = auth.join(data.address.split("//"))
            except:
                self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what))
                print "没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what)
                return self.results
            self.results.append("开始检出现金网%s代码"% what)
            print "开始检出现金网%s代码"% what
            grepo = self.repo
            log_repo = data.address
            repo = Repo(clone_dir)
            data_repo =data
        elif what == 'php' or what == 'js' or what == 'config':
            if what == 'php': clone_dir=self.php_dir
            if what == 'js': clone_dir=self.js_dir
            if what == 'config': clone_dir=self.config_dir
            try:
                data = git_coderepo.objects.get(platform=self.platform,classify=self.env,title="mn_"+what,ispublic=True)
                auth = "//"+data.user+":"+data.passwd+"@"
                self.repo = auth.join(data.address.split("//"))
            except:
                self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what))
                print "没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what)
                return self.results
            self.results.append("开始检出蛮牛%s代码"% what)
            print "开始检出蛮牛%s代码"% what
            grepo = self.repo
            log_repo = data.address
            repo = Repo(clone_dir)
            data_repo =data
        elif what == 'vue_php' or what == 'vue_pc' or what == 'vue_wap' or what == 'vue_config':
            if what == 'vue_php': 
                clone_dir=self.php_dir
                title = 'vue_mn_php'
            if what == 'vue_config': 
                clone_dir=self.config_dir
                title = 'vue_mn_config'
            if what == 'vue_pc': 
                clone_dir=self.pc_dir
                title = self.siteid+'_mn_pc'
            if what == 'vue_wap': 
                clone_dir=self.wap_dir
                title = self.siteid+'_mn_wap'
            try:
                data = git_coderepo.objects.get(platform=self.platform,classify=self.env,title=title)
                auth = "//"+data.user+":"+data.passwd+"@"
                self.repo = auth.join(data.address.split("//"))
            except:
                self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what))
                print "没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,what)
                return self.results
            self.results.append("开始检出VUE蛮牛%s代码"% what)
            print "开始检出VUE蛮牛%s代码"% what
            grepo = self.repo
            log_repo = data.address
            repo = Repo(clone_dir)
            data_repo =data
        else:
            clone_dir = self.web_dir
            try:
                data = git_coderepo.objects.get(platform=self.platform,classify=self.env,title=self.siteid,ispublic=False)
                auth = "//"+data.user+":"+data.passwd+"@"
                self.repo = auth.join(data.address.split("//"))
            except:
                self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,self.siteid))
                print "没有找到%s-%s-%s的git配置,停止发布！"% (self.platform,self.env,self.siteid)
                return self.results
            self.results.append("开始检出%s %s代码"% (self.platform,self.siteid))
            print "开始检出%s %s代码"% (self.platform,self.siteid)
            grepo = self.repo
            log_repo = data.address
            repo = Repo(clone_dir)  #检出目录
            data_repo = data


        print "检出地址:%s"% clone_dir
        if reversion:  #如果提供了版本则拉最新代码后检出到版本
            try:
                if branch != "master":
                    print "新分支，先切换主分支"
                    repo.git_checkout("master")
                    print "新分支，切换主分支完毕，开始拉取最新代码"
                    repo.git_pull() #新建分支先拉取在切换
                    print "新分支，拉取最新代码完成"
                print "bug定位--检出过程切换分支%s"% branch
                dingwei = repo.git_checkout(branch)
                repo.git_pull()
                print "bug定位--检出过程切换到版本号：%s"% reversion
                res = repo.git_checkout(reversion)
                self.results.append("切换分支%s,切换版本号%s"% (branch,reversion))
            except Exception as e: 
                print e
                res = "版本检出错误，请查看本地代码仓库是否存在"
                self.results.append("bug定位--检出过程版本错误：退出任务！")
                return False
            last_commit = reversion
        else:  #没有提供版本号则clone
            if data_repo.isexist == False:  #如果仓库在本地已存在export目录中则检出，否则clone
                genxin_code_dir(clone_dir)
                self.results.append("清空检出目录: %s,clone代码到本地"% clone_dir)
                res = repo.git_clone(grepo,clone_dir)
            else: #此条件只有公用public代码发布时才会用到
                if what is not "web":
                    genxin_code_dir(clone_dir)
                    res = repo.git_clone(grepo,clone_dir)
                    self.results.append("清空检出目录: %s,clone代码到本地"% clone_dir)
                else:
                    repo.git_checkout(branch)
                    self.results.append("切换到分支: %s"% branch)
                    res = repo.git_pull() 

            try:
                get_log = repo.git_log(identifier="--oneline")
                last_commit = get_log.strip()
            except:
                self.results.append("git仓库:%s 为空,没有代码,停止发布"% grepo)
                return False
        data_repo.reversion = last_commit[0:7]
        data_repo.branch = branch
        data_repo.isexist = True  #发布完成后应该更新此为真，公共代码会检查此项以避免重复clone代码
        data_repo.save()  #保存当前版本,将更新的版本号保存到git仓库中
        self.results.append("检出版本号：%s"% last_commit) #记录检出版本号
        self.results.append(res) #记录检出过程
        return self.results

    def update_release(self):
        datas = git_deploy.objects.get(pk=self.uuid)
        if self.method == "money_fabu":
            private_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).reversion
            php_pc_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="php_pc",ispublic=True).reversion
            php_mobile_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="php_mobile",ispublic=True).reversion
            js_pc_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="js_pc",ispublic=True).reversion
            js_mobile_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="js_mobile",ispublic=True).reversion
            web_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).branch
            php_pc_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="php_pc",ispublic=True).branch
            php_mobile_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="php_mobile",ispublic=True).branch
            js_pc_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="js_pc",ispublic=True).branch
            js_mobile_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="js_mobile",ispublic=True).branch
        elif self.method == "vue_manniu_fabu":
            pc_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name+"_mn_pc",ispublic=False).reversion
            wap_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name+"_mn_wap",ispublic=False).reversion
            php_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="vue_mn_php",ispublic=True).reversion
            config_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="vue_mn_config",ispublic=True).reversion
            pc_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name+"_mn_pc",ispublic=False).branch
            wap_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name+"_mn_wap",ispublic=False).branch
            php_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="vue_mn_php",ispublic=True).branch
            config_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="vue_mn_config",ispublic=True).branch
        elif self.method == "manniu_fabu":
            private_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).reversion
            php_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_php",ispublic=True).reversion
            js_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_js",ispublic=True).reversion
            config_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_config",ispublic=True).reversion
            web_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).branch
            php_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_php",ispublic=True).branch
            js_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_js",ispublic=True).branch
            config_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title="mn_config",ispublic=True).branch
        elif self.method == "java_fabu" or self.method == "op_fabu":
            private_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).reversion
            web_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).branch
        else:
            total_data = git_code_update.objects.filter(code_conf=datas,islog=False,isuse=False)
            if len(total_data) > 1:
                print "有多个未完成版本，取最新的未完成版本为有效版本"
                new_data = total_data.latest('ctime')
                git_code_update.objects.filter(code_conf=datas,islog=False,isuse=False).update(islog=True)
            elif len(total_data) == 1:
                new_data = git_code_update.objects.get(code_conf=datas,islog=False,isuse=False)
                print "最新版本为:%s,uuid=%s,版本号:%s"% (new_data.name,new_data.id,new_data.version)
            else:
                print "未发现未完成版本，取当前版本为有效版本"
                new_data = git_code_update.objects.get(code_conf=datas,islog=True,isuse=True)
            #所有更新都要使用的数据
            private_data = new_data.web_release
            web_branch = new_data.web_branches
            #现金网更新要使用的数据
            php_pc_data = new_data.php_pc_release
            php_mobile_data = new_data.php_moblie_release
            js_pc_data = new_data.js_pc_release
            js_mobile_data = new_data.js_mobile_release
            php_pc_branch = new_data.php_pc_branches
            php_mobile_branch = new_data.php_mobile_branches
            js_pc_branch = new_data.js_pc_branches
            js_mobile_branch = new_data.js_mobile_branches
            #蛮牛更新要使用的数据
            config_data = new_data.config_release
            config_branch = new_data.config_branches
            php_branch = new_data.php_pc_branches
            js_branch = new_data.js_pc_branches
            php_data = new_data.php_pc_release
            js_data = new_data.js_pc_release
            #VUE蛮牛使用的数据
            config_data = new_data.config_release
            config_branch = new_data.config_branches
            php_branch = new_data.php_pc_branches
            php_data = new_data.php_pc_release
            pc_data = new_data.js_pc_release
            pc_branch = new_data.js_pc_branches
            wap_data = new_data.js_mobile_release
            wap_branch = new_data.js_mobile_branches

        if self.platform == "现金网":
            datas.usepub = True
        #记录发布更新的版本日志
            last_commit = "日期：%s PHP电脑端(%s)：%s PHP手机端(%s)：%s VUE电脑端(%s)：%s VUE手机端(%s)：%s"% (self.now_time,php_pc_branch,php_pc_data,php_mobile_branch,php_mobile_data,js_pc_branch,js_pc_data,js_mobile_branch,js_mobile_data)
        elif self.platform == "蛮牛":
            datas.usepub = True
            last_commit = "日期：%s WEB(%s)：%s PHP-Pub代码(%s)：%s 前端-Pub代码(%s)：%s PHP-Config代码(%s)：%s"% (self.now_time,web_branch,private_data,php_branch,php_data,js_branch,js_data,config_branch,config_data)
        elif self.platform == "VUE蛮牛":
            datas.usepub = True
            last_commit = "日期：%s PC(%s)：%s WAP(%s): %s PHP(%s)：%s PHP配置文件(%s)：%s"% (self.now_time,pc_branch,pc_data,wap_branch,wap_data,php_branch,php_data,config_branch,config_data)
        else:
            datas.usepub = False
            last_commit = "日期：%s 分支：%s 版本号：%s"% (self.now_time,web_branch,private_data)
        datas.now_reversion = last_commit
        if datas.old_reversion:
            old_reversion = "\r\n".join(datas.old_reversion.split('\r\n')[0:30]) #保留一个月的更新记录,防止无限增长
            old_commits = last_commit + '\r\n' + old_reversion 
        else:
            old_commits = last_commit
        datas.old_reversion = old_commits
        datas.islock = False
        datas.save()
        #如果是第一次发布，初始化更新版本数据
        name = self.platform+"-"+datas.classify+"-"+datas.name+"-发布"

        if self.method == "money_fabu":
            updata = git_code_update(name=name,code_conf=datas,web_branches=web_branch,php_pc_branches=php_pc_branch,php_mobile_branches=php_mobile_branch,js_pc_branches=js_pc_branch,
                js_mobile_branches=js_mobile_branch,web_release=private_data,php_pc_release=php_pc_data,php_moblie_release=php_mobile_data,js_pc_release=js_pc_data,js_mobile_release=js_mobile_data,memo=name,
                isaudit=True,islog=True,isuse=True,last_version=last_commit)
            updata.save()
        elif self.method == "manniu_fabu":
            updata = git_code_update(name=name,code_conf=datas,web_branches=web_branch,php_pc_branches=php_branch,js_pc_branches=js_branch,config_branches=config_branch,
                web_release=private_data,php_pc_release=php_data,js_pc_release=js_data,config_release=config_data,memo=name,
                isaudit=True,islog=True,isuse=True,last_version=last_commit)
            updata.save()
        elif self.method == "vue_manniu_fabu":
            updata = git_code_update(name=name,code_conf=datas,php_pc_branches=php_branch,js_pc_branches=pc_branch,js_mobile_branches=wap_branch,config_branches=config_branch,
                php_pc_release=php_data,js_pc_release=pc_data,js_mobile_release=wap_data,config_release=config_data,memo=name,
                isaudit=True,islog=True,isuse=True,last_version=last_commit)
            updata.save()
        elif self.method == "op_fabu" or self.method == "java_fabu":
            updata = git_code_update(name=name,code_conf=datas,branch=web_branch,version=private_data,web_branches=web_branch,web_release=private_data,memo=name,isaudit=True,islog=True,isuse=True,last_version=last_commit)
            updata.save()
        else:
            pass
        self.results.append(last_commit)
        return self.results

    def merge_git(self):
        genxin_code_dir(self.merge_dir)  #清空或创建目录
        self.results.append("清空合并目录：%s"% self.merge_dir)
        if self.platform == "现金网":
            if self.env == 'test':
                cmd = '''\cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"
                    '''% (self.php_pc_dir,self.merge_dir,self.php_mobile_dir,self.merge_dir,
                        self.js_pc_dir,self.merge_dir,self.js_mobile_dir,self.merge_dir)
            else:
                cmd = '''\cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"
                    '''% (self.php_pc_dir,self.merge_dir,self.php_mobile_dir,self.merge_dir,
                        self.js_pc_dir,self.merge_dir,self.js_mobile_dir,self.merge_dir,self.config_dir,self.merge_dir)
        elif self.platform == "蛮牛":
            cmd = '''\cp -ar %s/* %s && \cp -ar %s/* %s &&  \cp -ar %s/* %s/public/ && \cp -ar %s/wcphpsec/config.php %s/m/php/ && echo "合并完成" || echo "合并失败，有错误！"
                '''% (self.web_dir,self.merge_dir,self.php_dir,self.merge_dir,self.js_dir,self.merge_dir,self.config_dir,self.merge_dir)
        elif self.platform == "VUE蛮牛":
            cmd = '''\cp -ar %s/* %s && \cp -ar %s/* %s &&  \cp -ar %s/* %s && \cp -ar %s/wcphpsec/config.php %s/m/php/ && echo "合并完成" || echo "合并失败，有错误！"
            '''% (self.pc_dir,self.merge_dir,self.wap_dir,self.merge_dir,self.php_dir,self.merge_dir,self.config_dir,self.merge_dir)
        else:
            cmd = '''\cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"'''% (self.web_dir,self.merge_dir)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        res = p.stdout.readlines()
        resok = ",".join(res)
        print ",".join(res)
        self.results.append(cmd)
        self.results.append("合并代码结果：%s"% resok)
        return self.results

    def ansible_rsync_web(self):
        self.results.append("开始推送代码至服务器")
        if self.platform == "现金网" or self.platform == "蛮牛" or self.platform == "VUE蛮牛":
            remotedir = self.remotedir +"/"+ self.siteid  #线上目录是在ops里面设置的目录加上siteid
        else:
            remotedir = self.remotedir

        exclude = genxin_exclude_file(self.exclude)

        if '\r\n' not in self.remoteip and '\n' in self.remoteip:
            self.remoteip = self.remoteip.replace('\n','\r\n')
        self.remoteip = self.remoteip.replace(' ','\r\n')

        print self.remoteip.split('\r\n')
        for i in self.remoteip.split('\r\n'):
            try:
                obj = Server.objects.get(ssh_host=i)
            except:
                self.results.append("CMDB中没有此服务器信息：%s,已跳过！"% i)
                continue
            if not ssh_check(i):
                self.results.append("服务器IP%s无法到达，已跳过！"% i)
                continue
            self.results.append("服务器：%s,目录：%s,排除文件：%s"% (i,remotedir,exclude))
            owner = "chown -R %s %s"% (self.owner,remotedir)
            unlock = "chattr -R -i /data/wwwroot/"
            lock = "chown -R %s /data/wwwroot/%s && chattr -R +i /data/wwwroot/ && find /data/wwwroot/ -maxdepth 6 -type d -name 'Logs' | xargs -i chattr -R -i {}"% (self.owner,self.siteid)
            if self.env == 'online' and self.platform == "现金网":
                command_unlock = ssh_cmd(i,unlock)
                self.results.append("解锁目录：%s"% unlock)
            #执行推送代码前命令
            if self.rsync_command:
                rsync_command_res = ssh_cmd(i,self.rsync_command)
                self.results.append("同步代码前要执行的命令：%s，执行结果：%s"% (self.rsync_command,rsync_command_res))
            #将代码从CMDB本地目录推送到服务器目录，需要此机器可以公钥访问源站
            task = MyTask(gen_resource(obj))
            rsync_res = task.genxin_rsync(self.merge_dir,remotedir,exclude) 
            if rsync_res["hosts"][i].has_key("msg"):
                self.results.append("同步代码返回msg：%s"% rsync_res["hosts"][i]["msg"])
            if rsync_res["hosts"][i].has_key("stdout_lines"):
                self.results.append("同步代码返回stdout_lines：%s"% rsync_res["hosts"][i]["stdout_lines"])
            #执行代码推送后命令
            if self.last_command:
                last_command_res = ssh_cmd(i,self.last_command)
                self.results.append("同步代码后要执行的命令：%s，执行结果：%s"% (self.last_command,last_command_res))
            #如果不是现金网的发布，此处应该省略
            if self.method == "money_fabu" or self.method == "manniu_fabu" or self.method == "vue_manniu_fabu":
                Logs_res = ssh_cmd(i,"mkdir -p %s/Logs && mkdir -p %s/m/Logs"% (remotedir,remotedir)) #第一次发布时创建Logs目录
            if self.env == 'online' and self.platform == "现金网":
                command_lock = ssh_cmd(i,lock)
                self.results.append("加锁目录：%s \n"% lock)
            else:
                command_lock = ssh_cmd(i,owner)
                self.results.append("添加属主：%s \n"% owner)
        return self.results

    def ansible_rsync_wwwroot(self):
        """大量站点更新,一次性执行推送,节约时间,节约服务器资源,避免频繁加锁解锁wwwroot目录"""
        self.results.append("开始推送代码至服务器")

        exclude = genxin_exclude_file(self.exclude) #同步排除文件队列处理
        remotedir = "/data/wwwroot/"
        if self.platform == "现金网":
            local_merge = "/data/moneyweb/" + self.env + "/merge/"
        elif self.platform == "VUE蛮牛":
            local_merge = "/data/manniuvue/" + self.env + "/merge/"
        elif self.platform == "蛮牛":
            local_merge = "/data/manniuweb/" + self.env + "/merge/"
        else:
            self.results.append("该项目不支持批量更新!")
            return self.results
        if '\r\n' not in self.remoteip and '\n' in self.remoteip:
            self.remoteip = self.remoteip.replace('\n','\r\n')
        self.remoteip = self.remoteip.replace(' ','\r\n')

        print self.remoteip.split('\r\n')
        for i in self.remoteip.split('\r\n'):
            try:
                obj = Server.objects.get(ssh_host=i)
            except:
                self.results.append("CMDB中没有此服务器信息：%s,已跳过！"% i)
                continue
            if not ssh_check(i):
                self.results.append("服务器IP%s无法到达，已跳过！"% i)
                continue
            self.results.append("服务器：%s,目录：%s,排除文件：%s"% (i,remotedir,exclude))
            owner = "chown -R %s %s"% (self.owner,remotedir)
            unlock = "chattr -R -i /data/wwwroot/"
            lock = "chown -R %s /data/wwwroot/ && chattr -R +i /data/wwwroot/"% self.owner
            if self.env == 'online' and self.platform == "现金网":
                command_unlock = ssh_cmd(i,unlock)
                self.results.append("解锁目录：%s"% unlock)
            #执行推送代码前命令
            if self.rsync_command:
                rsync_command_res = ssh_cmd(i,self.rsync_command)
                self.results.append("同步代码前要执行的命令：%s，执行结果：%s"% (self.rsync_command,rsync_command_res))
            #将代码从CMDB本地目录推送到服务器目录，需要此机器可以公钥访问源站
            task = MyTask(gen_resource(obj))
            rsync_res = task.genxin_rsync(local_merge,remotedir,exclude) 
            if rsync_res["hosts"][i].has_key("msg"):
                self.results.append("同步代码返回msg：%s"% rsync_res["hosts"][i]["msg"])
            if rsync_res["hosts"][i].has_key("stdout_lines"):
                self.results.append("同步代码返回stdout_lines：%s"% rsync_res["hosts"][i]["stdout_lines"])
            #执行代码推送后命令
            if self.last_command:
                last_command_res = ssh_cmd(i,self.last_command)
                self.results.append("同步代码后要执行的命令：%s，执行结果：%s"% (self.last_command,last_command_res))
            if self.env == 'online' and self.platform == "现金网":
                command_lock = ssh_cmd(i,lock)
                self.results.append("加锁目录：%s \n"% lock)
            else:
                command_lock = ssh_cmd(i,owner)
                self.results.append("添加属主：%s \n"% owner)
        return self.results



    def ansible_rsync_api(self,name,localfile,remotedir,remotefile,siteid,domains,pcdomains=None,mdomains=None):
        self.results.append("开始配置%s域名"% name)
        print "开始配置%s域名"% name
        try:
            if self.platform=="VUE蛮牛":
                remoteips = git_ops_configuration.objects.get(platform="蛮牛",classify=self.env,name=name).remoteip
            else:
                remoteips = git_ops_configuration.objects.get(platform=self.platform,classify=self.env,name=name).remoteip
            if '\r\n' not in remoteips and '\n' in remoteips:
                remoteips = remoteips.replace('\n','\r\n')
            remoteips = remoteips.replace(' ','\r\n')
            resource = gen_resource([Server.objects.get(ssh_host=i) for i in remoteips.split('\r\n')])
            playtask = MyPlayTask(resource)
            res = playtask.rsync_nginx_conf(localfile,remotedir,remotefile,siteid,domains,pcdomains=pcdomains,mdomains=mdomains)
            self.results.append("源站：%s 目录：%s,文件名：%s"% (remoteips,remotedir,remotefile))
            self.results.append("域名：%s"% domains)
            if res == 0:
                self.results.append("结果：成功！")
                print "结果：成功！"
            elif res == 1:
                self.results.append("结果：执行错误！")
                print "结果：执行错误！"
            else:
                self.results.append("结果：主机不可用！")
                print "结果：主机不可用！"
        except:
            self.results.append("未匹配到服务器,配置%s域名失败，跳过此处！"% name)
            print "未匹配到服务器,配置%s域名失败，跳过此处！"% name


    def web_front_domain(self):
        remote_dir = "/usr/local/nginx/conf/vhost/" #此处前期写死了，后期应该从business里面娶
        try:
            siteid = filter(str.isdigit,self.siteid) #只保留字符串中的数字
        except TypeError:
            siteid = filter(unicode.isdigit,self.siteid)
        print "当前siteid%s"% siteid
        #先找到域名
        business = Business.objects.get(nic_name=self.siteid,platform=self.platform) #某个项目的某个ID
        front_data = business.domain.filter(use=0,classify=self.env)
        vue_pc_domains = " ".join([i.name for i in front_data if "pc." in i.name])
        vue_m_domains = " ".join([i.name for i in front_data if "m." in i.name])
        front_domain = " ".join([i.name for i in front_data if i]) #组合所有的前端域名
        ag_data = business.domain.filter(use=1,classify=self.env)
        ag_domain = " ".join([i.name for i in ag_data if i])            #组合所有的ag域名
        backend_data = business.domain.filter(use=2,classify=self.env)  
        backend_domain = " ".join([i.name for i in backend_data if i])    #组合所有的后台域名
        # nav_data = business.domain.filter(use=3,classify=self.env)
        # nav_domain = " ".join([i.name for i in nav_data if i])

        if self.platform == "现金网":
            #同步源站域名
            name = "源站"
            domains = front_domain
            remotefile = self.siteid+".conf"
            port = siteid

            if self.env == "test":
                local_nginx_file = "front_test.conf"
                port = self.siteid
            else:
                local_nginx_file = "money_front_"+self.siteid[-1]+"_source.conf"

            self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)
            #现金网同步AG域名
            if self.env != "test":
                name = "AG"
                domains = ag_domain
                port = self.siteid
                local_nginx_file = "agent_"+self.env+".conf"
                remotefile = self.siteid+"_"+self.env+".conf"
                self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)

            #创建主A网灰度的时候创建线上后台nginx文件与灰度反代nginx文件
            if self.env == "huidu":
                if self.siteid[-1] not in ['b','c','d']: 
                    name = "后台"
                    domains = backend_domain
                    port = siteid
                    remotefile = self.siteid+".conf"
                    local_nginx_file = "backend.conf"
                    self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)
                    #同步现金网灰度源站反代域名
                    name = "源站反代"
                    domains = front_domain
                    port = siteid
                    local_nginx_file = "front_proxy.conf"
                    remotefile = siteid+".s1119.conf"
                    self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)


        if self.platform == "VUE蛮牛":
            name = "源站"
            domains = "-"
            remotefile = self.siteid+".conf"
            port = siteid
            if self.env == "huidu":
                local_nginx_file = "vue_mn_huidu_source.conf"
            elif self.env == "online":
                local_nginx_file = "vue_mn_online_source.conf"
            else:
                local_nginx_file = "vue_mn_test_source.conf"
            self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)

            #同步蛮牛源站反代域名
            if self.env != "test":
                name = "源站反代"
                domains = []
                for i in front_domain.split():
                    if not re.match("pc\.|m\.",i): #将pc和m开头的排除在外
                        domains.append(i)
                domains=" ".join(domains)
                if self.env == "huidu":
                    local_nginx_file = "vue_mn_huidu_front_proxy.conf"
                    remote_dir = "/usr/local/nginx/conf/vhost/huidu/"
                    remotefile = "huidu"+self.siteid+".conf"
                    self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)
                elif self.env == "online":
                    local_nginx_file = "vue_mn_online_front_proxy.conf"
                    remote_dir = "/usr/local/nginx/conf/vhost/"
                    remotefile = self.siteid+".conf"
                    self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains,pcdomains=vue_pc_domains,mdomains=vue_m_domains)

            #同步后台域名
            if self.env == "huidu":
                name = "后台"
                port = siteid
                domains = backend_domain
                local_nginx_file = "mn_backend.conf"
                remotefile = siteid+".conf"
                remote_dir = "/usr/local/nginx/conf/vhost/"
                self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)

            #同步AG和AG反代域名
            if self.env != "test": 
                name1 = "AG"
                name2 = "AG反代"
                remote_dir = "/usr/local/nginx/conf/vhost/"
                local_nginx_file1 = "mn_agent.conf"
                local_nginx_file2 = "mn_agent_proxy.conf"

                remotefile1 = "ag_"+siteid+".conf"
                remotefile2 = "ag"+siteid+".conf"

                port = self.siteid
                domains = ag_domain

                self.ansible_rsync_api(name1,local_nginx_file1,remote_dir,remotefile1,port,domains)
                self.ansible_rsync_api(name2,local_nginx_file2,remote_dir,remotefile2,port,domains)


        if self.platform == "蛮牛":
            #同步蛮牛源站
            name = "源站"
            domains = "-"
            remotefile = self.siteid+".conf"
            local_nginx_file = "mn_source.conf"
            port = self.siteid
            self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)
            #同步AG和AG反代域名
            if self.env != "test":
                name1 = "AG"
                name2 = "AG反代"

                local_nginx_file1 = "mn_agent.conf"
                local_nginx_file2 = "mn_agent_proxy.conf"

                remotefile1 = "ag_"+self.siteid+".conf"
                remotefile2 = "ag"+self.siteid+".conf"

                port = self.siteid
                domains = ag_domain

                self.ansible_rsync_api(name1,local_nginx_file1,remote_dir,remotefile1,port,domains)
                self.ansible_rsync_api(name2,local_nginx_file2,remote_dir,remotefile2,port,domains)

            #同步后台域名
            if self.env == "huidu":
                name = "后台"
                port = siteid
                domains = backend_domain
                local_nginx_file = "mn_backend.conf"
                remotefile = self.siteid+".conf"
                self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)

            #同步蛮牛源站反代域名
            if self.env != "test":
                name = "源站反代"
                domains = front_domain
                port = self.siteid
                if self.env == "huidu":
                    local_nginx_file = "mn_huidu_front_proxy.conf"
                    remote_dir = "/usr/local/nginx/conf/vhost/huidu/"
                    remotefile = "huidu"+self.siteid+".conf"
                elif self.env == "online":
                    local_nginx_file = "mn_online_front_proxy.conf"
                    remote_dir = "/usr/local/nginx/conf/vhost/"
                    remotefile = self.siteid+".conf"

                self.ansible_rsync_api(name,local_nginx_file,remote_dir,remotefile,port,domains)
        return self.results

@shared_task()
def git_fabu_task(uuid,myid):
    """给出id后，开始发布"""
    data = git_deploy.objects.get(pk=uuid)
    logs = []
    start = "%s,%s环境,开始发布%s"% (data.platform,data.classify,data.name)
    print start
    logs.append(start)
    #判断锁文件，有则等待，无则创建并发布，发布完成后删除锁文件
    lock_file = "/tmp/"+data.platform+"_"+data.classify+".lock"
    while os.path.isfile(lock_file):
        sleep(1)
    fo = open(lock_file,"wb")
    fo.write("locked")
    fo.close()
    logs.append("创建锁文件：%s"% lock_file)

    if data.deploy_update.filter(islog=True,isuse=True): #如果此项目有存在的版本号可用，则是已发项目，跳过发布过程
        logs.append("该项目不能重复发布！")
    else:
        if data.platform == "现金网":
            MyWeb = git_moneyweb_deploy(uuid,method="money_fabu")
        elif data.platform == "蛮牛":
            MyWeb = git_moneyweb_deploy(uuid,method="manniu_fabu")
        elif data.platform == "VUE蛮牛":
            MyWeb = git_moneyweb_deploy(uuid,method="vue_manniu_fabu")
        elif data.platform == "JAVA项目":
            MyWeb = git_moneyweb_deploy(uuid,method="java_fabu")
        else:
            MyWeb = git_moneyweb_deploy(uuid,method="op_fabu")
        logs = logs+MyWeb.results
    print "已完成发布%s"% data.name
    logs.append("已完成发布%s"% data.name)

    os.remove(lock_file)
    logs.append("删除锁文件：%s"% lock_file)

    #更新任务isend
    mydata = my_request_task.objects.get(pk=myid)
    mydata.status = "已完成" #即使发布不成功也会显示已完成,发布过程是黑箱无法获取结果
    mydata.isend = True
    mydata.save()
    #记录日志
    logdata = git_deploy_logs(name="发布",log="\r\n".join(logs),git_deploy=data)
    logdata.save()
    data = git_deploy.objects.get(pk=uuid)
    data.isaudit = True
    data.islog = True  #判断是否上线成功的字段
    if data.classify == "test": data.isops=True
    data.save()
    #创建复核任务
    if data.platform == "现金网" or data.platform == "蛮牛" or data.platform == "VUE蛮牛":
        try:
            auditor = git_deploy_audit.objects.get(platform="蛮牛",classify=data.classify,name="发布复核")
            confirm = my_request_task(name=mydata.name,types='fbconfirm',table_name="git_deploy",uuid=mydata.uuid,memo=mydata.memo,initiator=mydata.initiator,status="等待复核")
            confirm.save()
            task_distributing(confirm.id,auditor.id)
        except:
            data.isops=True
            data.save()

    return "celery FABU task is end"

@shared_task()
def git_update_task(uuid,myid):
    updata = git_code_update.objects.get(pk=uuid)
    data = updata.code_conf
    logs=[]
    start = "开始%s-%s环境-%s-%s更新\n"% (data.platform,data.classify,data.name,updata.method)
    logs.append(start)
    print start

    lock_file = "/tmp/"+data.platform+"_"+data.classify+".lock"
    while os.path.isfile(lock_file):
        sleep(1)
    fo = open(lock_file,"wb")
    fo.write("locked")
    fo.close()
    logs.append("创建锁文件：%s"% lock_file)

    MyWeb = git_moneyweb_deploy(data.id)
    print "更新方式为：%s"% updata.method

    if data.platform == "现金网":
        if updata.method == 'js_pc':
            MyWeb.export_git(what='js_mobile',branch=updata.js_mobile_branches,reversion=updata.js_mobile_release)
        elif updata.method == 'js_mobile':
            MyWeb.export_git(what='js_pc',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
    if data.platform == "VUE蛮牛":
        if updata.method != 'vue_pc':
            MyWeb.export_git(what='vue_pc',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
        if updata.method != 'vue_wap':
            MyWeb.export_git(what='vue_wap',branch=updata.js_mobile_branches,reversion=updata.js_mobile_release)
    export_reslut = MyWeb.export_git(what=updata.method,branch=updata.branch,reversion=updata.version)

    if export_reslut:
        MyWeb.update_release()
        MyWeb.merge_git()
        MyWeb.ansible_rsync_web()
        logs = logs+MyWeb.results
        end = "已完成%s"% updata.name
        status = "已完成"
    else:
        logs.append("%s版本检出错误，请查看本地代码仓库是否存在"% updata.method)
        end = "任务已失败：%s"% updata.name
        status = "更新任务失败"
        data.islock = False
        data.save()
    logs.append(end)
    print end

    os.remove(lock_file)
    logs.append("删除锁文件：%s"% lock_file)
    #更新任务isend
    mydata = my_request_task.objects.get(pk=myid)
    mydata.status = status
    mydata.isend = True
    mydata.save()
    #记录日志
    logdata = git_deploy_logs(name="更新",log="\r\n".join(logs),git_deploy=data,update=updata.id)
    logdata.save()
    #标记当前使用版本
    if export_reslut:
        git_code_update.objects.filter(code_conf=data,islog=True,isuse=True).update(isuse=False) #先让所有版本不可用，然后标记当前版本可用
        updata.islog = True
        updata.isuse = True
    else:
        updata.islog = True
    updata.last_version = data.now_reversion #记住上一次版本信息
    updata.isaudit = True
    updata.save()
    return "celery GENGXIN task is end"

@shared_task()
def git_update_public_task(uuid,myid,platform="现金网"):
    updata = git_code_update.objects.get(pk=uuid)
    if "huidu" in updata.name:
        env = "huidu"
    elif "online" in updata.name:
        env = "online"
    else:
        env = "test"
    logs=[]
    #加锁
    lock_file = "/tmp/"+platform+"_"+env+".lock"
    while os.path.isfile(lock_file):
        sleep(1)
    fo = open(lock_file,"wb")
    fo.write("locked")
    fo.close()
    logs.append("创建锁文件：%s"% lock_file)

    datas = git_deploy.objects.filter(platform=platform,classify=env,isops=True,islog=True,usepub=True) #迁移的时候别忘记把所有的项目usepub项更新为真
    datas.update(islock=True) #全局锁

    counts=[]
    for data in datas:
        start = "%s公用代码-%s环境-%s-%s更新"% (platform,env,data.name,updata.method)
        logs.append(start)
        print start
        latest_update = data.deploy_update.get(islog=True,isuse=True) #获取上一个版本实例
        #现金网使用项
        php_pc_release = latest_update.php_pc_release
        php_moblie_release = latest_update.php_moblie_release
        js_pc_release = latest_update.js_pc_release
        js_mobile_release = latest_update.js_mobile_release
        php_pc_branches = latest_update.php_pc_branches
        php_mobile_branches = latest_update.php_mobile_branches
        js_pc_branches = latest_update.js_pc_branches
        js_mobile_branches = latest_update.js_mobile_branches
        #蛮牛使用项
        config_branches = latest_update.config_branches
        config_release = latest_update.config_release

        if updata.method == "php_pc":
            php_pc_release = updata.version
            php_pc_branches = updata.branch
        elif updata.method == "js_pc":
            js_pc_release = updata.version
            js_pc_branches = updata.branch
        elif updata.method == "php_mobile":
            php_moblie_release = updata.version
            php_mobile_branches = updata.branch
        elif updata.method == "js_mobile":
            js_mobile_release = updata.version
            js_mobile_branches = updata.branch
        elif updata.method == "php" or updata.method == "vue_php":
            php_pc_release = updata.version
            php_pc_branches = updata.branch
        elif updata.method == "js":
            js_pc_release = updata.version
            js_pc_branches = updata.branch
        elif updata.method == "config" or updata.method == "vue_config":
            config_branches = updata.branch
            config_release = updata.version

        name = data.platform+"-"+data.classify+"-"+data.name+"-"+updata.method+"-更新"
        new_data = git_code_update(name=name,code_conf=data,method=updata.method,version=updata.version,branch=updata.branch,web_release=latest_update.web_release,
            php_pc_release=php_pc_release,js_pc_release=js_pc_release,php_moblie_release=php_moblie_release,js_mobile_release=js_mobile_release,config_release=config_release,
            web_branches=latest_update.web_branches,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,config_branches=config_branches,
            js_mobile_branches=js_mobile_branches,memo=updata.memo,isaudit=True,isurgent=updata.isurgent,last_version=data.now_reversion)
        new_data.save()
        #开始更新
        MyWeb = git_moneyweb_deploy(data.id)
        #MyWeb.export_config(branch="master")
        if platform=="现金网":
            MyWeb.export_git(what='js_mobile',branch=latest_update.js_mobile_branches,reversion=latest_update.js_mobile_release) #如果查看分支后版本会错乱,所以取上个版本的web版本号
            MyWeb.export_git(what="js_pc",branch=latest_update.js_pc_branches,reversion=latest_update.js_pc_release)
        if data.platform == "VUE蛮牛":
            MyWeb.export_git(what='vue_pc',branch=latest_update.js_pc_branches,reversion=latest_update.js_pc_release)
            MyWeb.export_git(what='vue_wap',branch=latest_update.js_mobile_branches,reversion=latest_update.js_mobile_release)
        export_reslut = MyWeb.export_git(what=updata.method,branch=updata.branch,reversion=updata.version) #取更新的公共代码版本号
        # if data.platform == "现金网":
        #     MyWeb.export_git(what='web',branch=latest_update.web_branches,reversion=latest_update.web_release) #取上个版本的web版本号
        #     export_reslut = MyWeb.export_git(what="php_pc",branch=new_data.php_pc_branches,reversion=new_data.php_pc_release) #取更新的公共代码版本号
        #     export_reslut = MyWeb.export_git(what="php_mobile",branch=new_data.php_mobile_branches,reversion=new_data.php_moblie_release) #取更新的公共代码版本号
        #     export_reslut = MyWeb.export_git(what="js_pc",branch=new_data.js_pc_branches,reversion=new_data.js_pc_release) #取更新的公共代码版本号
        #     export_reslut = MyWeb.export_git(what="js_mobile",branch=new_data.js_mobile_branches,reversion=new_data.js_mobile_release) #取更新的公共代码版本号
        # else:
        #     MyWeb.export_git(what='web',branch=latest_update.web_branches,reversion=latest_update.web_release) #取上个版本的web版本号
        #     export_reslut = MyWeb.export_git(what=updata.method,branch=updata.branch,reversion=updata.version) #取更新的公共代码版本号
        if export_reslut:
            MyWeb.update_release()  #此步骤已经解锁data
            MyWeb.merge_git()
            logs = logs+MyWeb.results
            end = "已完成：%s \n"% name
            logs.append(end)
            latest_update.isuse=False #标记当前版本失效，创建新版本
            latest_update.save()
            new_data.islog = True
            new_data.isuse = True
            new_data.save()
        else:
            counts.append(data.name)
            logs.append("%s版本检出错误，请查看本地代码仓库是否存在"% updata.method)
            end = "任务已失败：%s \n"% name
            print end
            data.islock = False
            data.save()
            new_data.islog = True
            new_data.save()
            logs.append(end)
            continue
    MyWeb.ansible_rsync_wwwroot()
    print "已完成%s"% updata.name
    if counts:
        failed = " ".join(counts)
        logs.append("这些站点：%s 更新失败，请联系运维人员查找原因！"% failed)
    logs.append("已完成%s"% updata.name)
    #更新任务isend
    mydata = my_request_task.objects.get(pk=myid)
    mydata.status = "已完成"
    mydata.isend = True
    mydata.save()

    os.remove(lock_file)
    logs.append("删除锁文件：%s"% lock_file)
    
    #记录日志
    logdata = git_deploy_logs(name="更新",log="\r\n".join(logs),update=updata.id)
    logdata.save()
    updata.islog = True
    updata.isaudit = True
    updata.save()
    return "celery GENGXIN-PUBLIC task is end"

@shared_task()
def commit_details_task(uuid,env=None,platform=None):
    #此项以无调用，将来移除
    if platform == "manniu":
        updata = manniu_update.objects.get(pk=uuid)
        data = updata.project
    else:
        updata = git_code_update.objects.get(pk=uuid)
        data = updata.code_conf
    if platform == "manniu":
        if data:
            MyWeb = manniu_web_deploy(data.id)
        else:
            MyWeb = manniu_web_deploy(manniu_deploy.objects.filter(platform="蛮牛",classify=env,islog=True)[0].id)
        res = MyWeb.commit_details(what=updata.method,reversion=updata.release,branch=updata.branch)
    else:
        if data:
            MyWeb = git_moneyweb_deploy(data.id)
        else:
            MyWeb = git_moneyweb_deploy(git_deploy.objects.filter(platform="现金网",classify=env,islog=True)[0].id)
        res = MyWeb.commit_details(what=updata.method,reversion=updata.version,branch=updata.branch)
    updata.details = res
    updata.save()
    return "Commit_Details task is end"

@shared_task()
def git_batch_update_task(myid,platform="现金网",memos=None):
    mydata = my_request_task.objects.get(pk=myid)
    types = mydata.types.split("-")
    platform = types[0]
    classify = types[1]
    batch = types[2]
    method = types[3]

    logs=[]
    start = "开始%s\n"% mydata.name
    logs.append(start)
    print start

    lock_file = "/tmp/"+platform+"_"+classify+".lock"
    while os.path.isfile(lock_file):
        sleep(1)
    fo = open(lock_file,"wb")
    fo.write("locked")
    fo.close()
    logs.append("创建锁文件：%s"% lock_file)

    if not memos: memos = eval(mydata.memo)
    for key,value in memos.items():
        updata = change_version_old_to_new(key,platform,classify,method,value)
        data = git_deploy.objects.get(name=key,platform=platform,classify=classify,isops=True,islog=True)
        MyWeb = git_moneyweb_deploy(data.id)
        if platform == "现金网":
            export_reslut = MyWeb.export_git(what='js_pc',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
            export_reslut = MyWeb.export_git(what='js_mobile',branch=updata.js_mobile_branches,reversion=updata.js_mobile_release)
        else:
            export_reslut = MyWeb.export_git(what=method,branch="master",reversion=value) #需要判断是不是vue蛮牛或者现金网,pc和手机都要更新,但是这里先不处理
        
        if export_reslut:
            MyWeb.update_release()
            MyWeb.merge_git()
            logs = logs+MyWeb.results
            end = "已完成%s"% updata.name
            status = "已完成"
            data.deploy_update.filter(isuse=True).update(isuse=False)
            updata.isuse = True
        else:
            logs.append("%s版本检出错误，请查看本地代码仓库是否存在"% updata.method)
            end = "任务已失败：%s"% updata.name
            status = "更新任务失败"
            data.islock=False
            data.save()
        updata.islog = True
        updata.save()
        logs.append(end)
        print end
    MyWeb.ansible_rsync_wwwroot()
    os.remove(lock_file)
    logs.append("删除锁文件：%s"% lock_file)
    #更新任务isend

    mydata.status = status
    mydata.isend = True
    mydata.save()
    #记录日志
    logdata = git_deploy_logs(name="更新",log="\r\n".join(logs),git_deploy=data,update=mydata.uuid)
    logdata.save()
    return "celery Batch_gengxin_task is end"