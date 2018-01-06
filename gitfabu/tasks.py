#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task

from api.git_api import Repo
from api.ssh_api import ssh_cmd,ssh_check
from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
import time
import os
from time import sleep
import subprocess
from assets.models import Server
from api.ansible_api import MyTask, MyPlayTask
from gitfabu.models import git_deploy,my_request_task,git_coderepo,git_ops_configuration,git_deploy_logs,git_code_update
from business.models import DomainName,Business

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
            self.merge_dir = "/data/manniuweb/" + self.env + "/merge/" + self.siteid
            self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址
            self.php_dir = self.base_export_dir + self.siteid + "_mn_php" #公共php代码pc端检出地址
            self.js_dir = self.base_export_dir + self.siteid + "_mn_js" #公共js代码pc端检出地址
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
            self.export_git(what='web')
            if self.usepub:
                self.export_git(what='php_pc')
                self.export_git(what='js_pc')
                self.export_git(what='php_mobile')
                self.export_git(what='js_mobile')
                if not self.env == "test":
                    self.export_config(branch="master")
            self.update_release()
            self.merge_git()
            self.ansible_rsync_web()
            if data.conf_domain:
                self.web_front_domain()
        elif self.method == "manniu_fabu":
            print "发布蛮牛web项目"
            self.export_git(what='web')
            self.export_git(what='php')
            self.export_git(what='js')
            self.export_git(what='config')
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
            if data.conf_domain:
                self.web_front_domain()
        elif self.method == "java_fabu":
            self.export_git(what='java')
            self.update_release()
            self.merge_git()
            self.ansible_rsync_web()
            if data.conf_domain:
                self.web_front_domain()

    def deploy_all_branch(self,what='web'):
        if what == 'php_pc':
            repo = Repo(self.base_export_dir+"php_pc/")
        elif what == 'php_mobile':
            repo = Repo(self.base_export_dir+ "php_mobile/")
        elif what == 'js_pc':
            repo = Repo(self.base_export_dir+ "js_pc/")
        elif what == 'js_mobile':
            repo = Repo(self.base_export_dir+ "js_mobile/")
        elif what == 'php':
            repo = Repo(self.base_export_dir+ "mn_php/")
        elif what == 'js':
            repo = Repo(self.base_export_dir+ "mn_js/")
        elif what == 'config':
            repo = Repo(self.base_export_dir+ "mn_config/")
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
            repo = Repo(self.base_export_dir+ "js_pc/")
        elif what == 'js_mobile':
            repo = Repo(self.base_export_dir+ "js_mobile/")
        elif what == 'php':
            repo = Repo(self.base_export_dir+ "mn_php/")
        elif what == 'js':
            repo = Repo(self.base_export_dir+ "mn_js/")
        elif what == 'config':
            repo = Repo(self.base_export_dir+ "mn_config/")
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
        res = repo.git_clone(url,self.config_dir)
        self.results.append("检出%s配置文件"% self.siteid)
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

        if reversion:  #如果提供了版本则拉最新代码后检出到版本
            try:
                print "bug定位--检出过程切换分支%s"% branch
                repo.git_pull() #新建分支先拉取在切换
                repo.git_checkout(branch)
                res = repo.git_checkout(reversion)
                print "bug定位--检出过程切换到版本号：%s"% reversion
                res1 = "切换分支%s,切换版本号%s"% (branch,reversion)
            except:
                res = "版本检出错误，请查看本地代码仓库是否存在"
                res1 = "bug定位--检出过程版本错误：退出任务！"
                return False
            last_commit = reversion
        else:  #没有提供版本号则clone
            if data_repo.isexist == False:  #如果仓库在本地已存在export目录中则检出，否则clone
                genxin_code_dir(clone_dir)
                res1 = "清空检出目录: %s,clone代码到本地"% clone_dir
                res = repo.git_clone(grepo,clone_dir)
                last_commit = repo.show_commit()[0]
            else: #此条件只有公用public代码发布时才会用到
                if what is not "web":
                    genxin_code_dir(clone_dir)
                    res = repo.git_clone(grepo,clone_dir)
                    res1 = "清空检出目录: %s,clone代码到本地"% clone_dir
                else:
                    repo.git_checkout(branch)
                    res1 = "切换到分支: %s"% branch
                    res = repo.git_pull() 
                last_commit = repo.show_commit()[0]
        data_repo.reversion = last_commit[0:7]
        data_repo.branch = branch
        data_repo.isexist = True  #发布完成后应该更新此为真，公共代码会检查此项以避免重复clone代码
        data_repo.save()  #保存当前版本,将更新的版本号保存到git仓库中
        self.results.append(res1) #记录检出分支日志
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
            try:
                new_data = git_code_update.objects.get(code_conf=datas,islog=False,isuse=False) #使用刚创建还没有完成的更新版本为最新版本
            except:
                print "有失败的更新导致的版本冲突，现在取最新的未完成版本为有效版本"
                new_data = git_code_update.objects.filter(code_conf=datas,islog=False,isuse=False).latest('ctime')
                git_code_update.objects.filter(code_conf=datas,islog=False,isuse=False).update(islog=True)
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

        if self.platform == "现金网":
            datas.usepub = True
        #记录发布更新的版本日志
            last_commit = "日期：%s WEB(%s)：%s PHP电脑端(%s)：%s PHP手机端(%s)：%s JS电脑端(%s)：%s JS手机端(%s)：%s"% (self.now_time,web_branch,private_data,php_pc_branch,php_pc_data,php_mobile_branch,php_mobile_data,js_pc_branch,js_pc_data,js_mobile_branch,js_mobile_data)
        elif self.platform == "蛮牛":
            datas.usepub = True
            last_commit = "日期：%s WEB(%s)：%s PHP-Pub代码(%s)：%s 前端-Pub代码(%s)：%s PHP-Config代码(%s)：%s"% (self.now_time,web_branch,private_data,php_branch,php_data,js_branch,js_data,config_branch,config_data)
        else:
            datas.usepub = False
            last_commit = "日期：%s 分支：%s 版本号：%s"% (self.now_time,web_branch,private_data)
        datas.now_reversion = last_commit
        if datas.old_reversion:
            old_commits = last_commit + '\r\n' + datas.old_reversion 
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
        elif self.method == "op_fabu" or self.method == "java_fabu":
            updata = git_code_update(name=name,code_conf=datas,branch=web_branch,web_branches=web_branch,web_release=private_data,version=private_data,memo=name,isaudit=True,islog=True,isuse=True)
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
                cmd = '''\cp -ar %s/*  %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"
                    '''% (self.web_dir,self.merge_dir,self.php_pc_dir,self.merge_dir,self.php_mobile_dir,self.merge_dir,
                        self.js_pc_dir,self.merge_dir,self.js_mobile_dir,self.merge_dir)
            else:
                cmd = '''\cp -ar %s/*  %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"
                    '''% (self.web_dir,self.merge_dir,self.php_pc_dir,self.merge_dir,self.php_mobile_dir,self.merge_dir,
                        self.js_pc_dir,self.merge_dir,self.js_mobile_dir,self.merge_dir,self.config_dir,self.merge_dir)
        elif self.platform == "蛮牛":
            cmd = '''\cp -ar %s/* %s && \cp -ar %s/* %s &&  \cp -ar %s/* %s/public/ && \cp -ar %s/wcphpsec/config.php %s/m/php/ && echo "合并完成" || echo "合并失败，有错误！"
                '''% (self.web_dir,self.merge_dir,self.php_dir,self.merge_dir,self.js_dir,self.merge_dir,self.config_dir,self.merge_dir)
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
        remotedir = self.remotedir +"/"+ self.siteid  #线上目录是在ops里面设置的目录加上siteid
        exclude = genxin_exclude_file(self.exclude)
        print self.remoteip.split('\r\n')
        for i in self.remoteip.split('\r\n'):
            try:
                obj = Server.objects.get(ssh_host=i)
            except:
                self.results.append("CMDB中没有此服务器信息：%s,已跳过！"% i)
                continue
            if not ssh_check(i):
                self.results.append("现金网源站%s不可用，已跳过！"% i)
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
            if self.method == "money_fabu" or self.method == "manniu_fabu":
                Logs_res = ssh_cmd(i,"mkdir -p %s/Logs && mkdir -p %s/m/Logs"% (remotedir,remotedir)) #第一次发布时创建Logs目录
            if self.env == 'online' and self.platform == "现金网":
                command_lock = ssh_cmd(i,lock)
                self.results.append("加锁目录：%s \n"% lock)
            else:
                command_lock = ssh_cmd(i,owner)
                self.results.append("添加属主：%s \n"% owner)
        return self.results

    def web_front_domain(self):
        remote_dir = "/usr/local/nginx/conf/vhost/" #此处前期写死了，后期应该从business里面娶
        siteid = self.siteid.replace('f','')
        frontname = self.env_ch+"-"+self.siteid+"前端域名" #灰度的前端域名与前端反代节点域名一样
        agname = self.env_ch+"-"+self.siteid+"AG域名"
        backendname = self.env_ch+"-"+self.siteid+"后台域名"
        #先找到域名
        business = Business.objects.get(nic_name=self.siteid,platform=self.platform) #某个项目的某个ID
        front_data = business.domain.filter(use=0,classify=self.env)
        front_domain = " ".join([i.name for i in front_data if i])
        ag_data = business.domain.filter(use=1,classify=self.env)
        ag_domain = " ".join([i.name for i in ag_data if i])
        backend_data = business.domain.filter(use=2,classify=self.env)
        backend_domain = " ".join([i.name for i in backend_data if i])
        nav_data = business.domain.filter(use=3,classify=self.env)
        nav_domain = " ".join([i.name for i in nav_data if i])

        self.results.append("开始域名配置")
        #开始找到源站的ip
        front_remoteips = self.remoteip
        if self.env == "huidu" or self.env == "online": #测试环境不需要ag与后台
            try:
                ag_remoteips = git_ops_configuration.objects.get(platform=self.platform,classify=self.env,name="AG").remoteip
            except:
                self.results.append("ERROR:%s-%s-AG没有配置"% (self.platform,self.env))
            try:
                backend_remoteips = git_ops_configuration.objects.get(platform=self.platform,classify=self.env,name="后台").remoteip
            except:
                self.results.append("ERROR:%s-%s-后台没有配置"% (self.platform,self.env))
        #同步前端域名
        if self.platform == "现金网":
            if self.env == "test":
                local_nginx_file = "front_test.conf"
            else:
                if "f" in self.siteid:
                    local_nginx_file = "front_fu.conf"
                else:
                    local_nginx_file = "front_zhu.conf"
        elif self.platform == "蛮牛":
            local_nginx_file = "mn_source.conf"
        #rsync_nginx_conf参数(localfile,remotedir,remotefile,siteid,domains)
        try:
            resource = gen_resource([Server.objects.get(ssh_host=i) for i in front_remoteips.split('\r\n')])
            playtask = MyPlayTask(resource)
            if self.platform == "现金网":
                if self.env == "test":
                    res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,self.siteid+".conf",self.siteid,front_domain)
                else:
                    res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,self.siteid+".conf",siteid,front_domain)
            elif self.platform == "蛮牛":
                res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,self.siteid+".conf",self.siteid,"-")

            self.results.append("源站：%s 文件名：%s"% (front_remoteips,remote_dir+self.siteid+".conf"))
            self.results.append("域名：%s"% front_domain)
            if res == 0:
                self.results.append("结果：成功！")
            elif res == 1:
                self.results.append("结果：执行错误！")
            else:
                self.results.append("结果：主机不可用！")
        except:
            self.results.append("配置源站域名失败，任务结束！")
            return self.results

        #同步AG域名
        if self.platform == "现金网":
            if self.env == "huidu" or self.env == "online":
                if self.env == "huidu" and self.platform=="现金网":
                    local_nginx_file = "agent_huidu.conf"
                    filename = self.siteid+"_huidu.conf"
                elif self.env == "online" and self.platform=="现金网":
                    local_nginx_file = "agent.conf"
                    filename = self.siteid+"_online.conf"
                elif self.env == "huidu" and self.platform=="蛮牛":
                    local_nginx_file = "mn_huidu_agent.conf"
                    filename = self.siteid+"_huidu.conf"
                elif self.env == "online" and self.platform=="蛮牛":
                    local_nginx_file = "mn_agent.conf"
                    filename = self.siteid+"_online.conf"
                try:
                    resource = gen_resource([Server.objects.get(ssh_host=i) for i in ag_remoteips.split('\r\n')])
                    playtask = MyPlayTask(resource)
                    res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,filename,self.siteid,ag_domain)
                    self.results.append("AG站：%s 文件名：%s"% (ag_remoteips,remote_dir+filename))
                    self.results.append("域名：%s"% ag_domain)
                    if res == 0:
                        self.results.append("结果：成功！")
                    elif res == 1:
                        self.results.append("结果：执行错误！")
                    else:
                        self.results.append("结果：主机不可用！")
                except:
                    self.results.append("配置AG域名失败，任务结束！")
                    return self.results
            #同步后台域名
            if self.env == "huidu":
                if "f" not in self.siteid: 
                    if self.platform == "现金网": local_nginx_file = "backend.conf"
                    if self.platform == "蛮牛": local_nginx_file = "mn_backend.conf"
                    try:
                        resource = gen_resource([Server.objects.get(ssh_host=i) for i in backend_remoteips.split('\r\n')])
                        playtask = MyPlayTask(resource)
                        res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,self.siteid+".conf",siteid,backend_domain)
                        self.results.append("后台站：%s 文件名：%s"% (backend_remoteips,remote_dir+self.siteid+".conf"))
                        self.results.append("域名：%s"% backend_domain)
                        if res == 0:
                            self.results.append("结果：成功！")
                        elif res == 1:
                            self.results.append("结果：执行错误！")
                        else:
                            self.results.append("结果：主机不可用！")
                    except:
                        self.results.append("配置后台域名失败，任务结束！")
                        return self.results
            #同步现金网源站反代域名
            if self.env == "huidu":
                if "f" not in self.siteid:
                    local_nginx_file = "front_proxy.conf"
                    remote_nginx_file = siteid+".s1119.conf"
                    try:
                        proxy_remoteips = git_ops_configuration.objects.get(platform="现金网",classify=self.env,name="源站反代").remoteip
                        resource = gen_resource([Server.objects.get(ssh_host=i) for i in proxy_remoteips.split('\r\n')])
                        playtask = MyPlayTask(resource)
                        playtask.rsync_nginx_conf(local_nginx_file,remote_dir,remote_nginx_file,siteid,front_domain)
                        self.results.append("源站反代站：%s 文件名：%s"% (proxy_remoteips,remote_dir+remote_nginx_file))
                        self.results.append("域名：%s"% front_domain)
                        if res == 0:
                            self.results.append("结果：成功！")
                        elif res == 1:
                            self.results.append("结果：执行错误！")
                        else:
                            self.results.append("结果：主机不可用！")
                    except:
                        self.results.append("ERROR:现金网-%s-源站反代没有配置"% self.env)
                        self.results.append("配置源站反代域名失败，任务结束！")
                        return self.results
        #同步蛮牛源站反代域名
        if self.platform == "蛮牛":
            if self.env == "online":
                local_nginx_file = "mn_agent.conf"
                filename = "ag_"+self.siteid+".conf"
                try:
                    resource = gen_resource([Server.objects.get(ssh_host=i) for i in ag_remoteips.split('\r\n')])
                    playtask = MyPlayTask(resource)
                    res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,filename,self.siteid,ag_domain)
                    self.results.append("AG站：%s 文件名：%s"% (ag_remoteips,remote_dir+filename))
                    self.results.append("域名：%s"% ag_domain)
                    if res == 0:
                        self.results.append("结果：成功！")
                    elif res == 1:
                        self.results.append("结果：执行错误！")
                    else:
                        self.results.append("结果：主机不可用！")
                except:
                    self.results.append("配置AG域名失败，任务结束！")
                    return self.results
            #同步后台域名
            if self.env == "online":
                local_nginx_file = "mn_backend.conf"
                try:
                    resource = gen_resource([Server.objects.get(ssh_host=i) for i in backend_remoteips.split('\r\n')])
                    playtask = MyPlayTask(resource)
                    res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,self.siteid+".conf",siteid,backend_domain)
                    self.results.append("后台站：%s 文件名：%s"% (backend_remoteips,remote_dir+self.siteid+".conf"))
                    self.results.append("域名：%s"% backend_domain)
                    if res == 0:
                        self.results.append("结果：成功！")
                    elif res == 1:
                        self.results.append("结果：执行错误！")
                    else:
                        self.results.append("结果：主机不可用！")
                except:
                    self.results.append("配置后台域名失败，任务结束！")
                    return self.results
            if self.env == "huidu":
                local_nginx_file = "mn_huidu_front_proxy.conf"
                remote_dir = "/usr/local/nginx/conf/vhost/huidu/"
                remote_nginx_file = "huidu"+self.siteid+".conf"
                proxy = True
            elif self.env == "online":
                proxy = True
                local_nginx_file = "mn_online_front_proxy.conf"
                remote_dir = "/usr/local/nginx/conf/vhost/"
                remote_nginx_file = self.siteid+".conf"
            else:
                proxy = False
            if proxy:
                try:
                    proxy_remoteips = git_ops_configuration.objects.get(platform="蛮牛",classify=self.env,name="源站反代").remoteip
                    resource = gen_resource([Server.objects.get(ssh_host=i) for i in proxy_remoteips.split('\r\n')])
                    playtask = MyPlayTask(resource)
                    playtask.rsync_nginx_conf(local_nginx_file,remote_dir,remote_nginx_file,self.siteid,front_domain)
                    self.results.append("源站反代站：%s 文件名：%s"% (proxy_remoteips,remote_dir+remote_nginx_file))
                    self.results.append("域名：%s"% front_domain)
                    if res == 0:
                        self.results.append("结果：成功！")
                    elif res == 1:
                        self.results.append("结果：执行错误！")
                    else:
                        self.results.append("结果：主机不可用！")
                except:
                    self.results.append("ERROR:现金网-%s-源站反代没有配置"% self.env)
                    self.results.append("配置源站反代域名失败，任务结束！")
                    return self.results
        return self.results

@shared_task()
def git_fabu_task(uuid,myid):
    """给出id后，开始发布"""
    data = git_deploy.objects.get(pk=uuid)
    logs = []
    start = "%s,%s环境,开始发布%s"% (data.platform,data.classify,data.name)
    print start
    logs.append(start)
    if data.deploy_update.filter(islog=True,isuse=True): #如果此项目有存在的版本号可用，则是已发项目，跳过发布过程
        logs.append("该项目不能重复发布！")
    else:
        if data.platform == "现金网":
            MyWeb = git_moneyweb_deploy(uuid,method="money_fabu")
        elif data.platform == "蛮牛":
            MyWeb = git_moneyweb_deploy(uuid,method="manniu_fabu")
        elif data.platform == "JAVA项目":
            MyWeb = git_moneyweb_deploy(uuid,method="java_fabu")
        else:
            MyWeb = git_moneyweb_deploy(uuid,method="op_fabu")
        logs = logs+MyWeb.results
    print "已完成发布%s"% data.name
    logs.append("已完成发布%s"% data.name)
    #更新任务isend
    mydata = my_request_task.objects.get(pk=myid)
    mydata.status = "已完成"
    mydata.isend = True
    mydata.save()
    #记录日志
    logdata = git_deploy_logs(name="发布",log="\r\n".join(logs),git_deploy=data)
    logdata.save()
    data = git_deploy.objects.get(pk=uuid)
    data.islog = True  #判断是否上线成功的字段
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
    MyWeb = git_moneyweb_deploy(data.id)
    print "更新方式为：%s"% updata.method
    print type(updata.method)
    if updata.method != 'web':
        print "非web更新，需要执行web代码"
        MyWeb.export_git(what='web',branch=updata.web_branches,reversion=updata.web_release)
    export_reslut = MyWeb.export_git(what=updata.method,branch=updata.branch,reversion=updata.version)
    # if data.platform == "现金网":  #cmdb迁移之后要使用下面代码，以保证存在的站更新不会错乱
    #     MyWeb.export_git(what='web',branch=updata.web_branches,reversion=updata.web_release)
    #     MyWeb.export_git(what='php_pc',branch=updata.php_pc_branches,reversion=updata.php_pc_release)
    #     MyWeb.export_git(what='php_mobile',branch=updata.php_mobile_branches,reversion=updata.php_moblie_release)
    #     MyWeb.export_git(what='js_pc',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
    #     MyWeb.export_git(what='js_mobile',branch=updata.js_mobile_branches,reversion=updata.js_mobile_release)
    #     export_reslut = True
    # elif data.platform == "蛮牛":
    #     MyWeb.export_git(what='web',branch=updata.web_branches,reversion=updata.web_release)
    #     MyWeb.export_git(what='php',branch=updata.php_pc_branches,reversion=updata.php_pc_release)
    #     MyWeb.export_git(what='js',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
    #     MyWeb.export_git(what='config',branch=updata.config_branches,reversion=updata.config_release)
    #     export_reslut = True
    # else:
    #     export_reslut = MyWeb.export_git(what=updata.method,branch=updata.branch,reversion=updata.version) #必须保证公共代码不会无故更新，必须每个项目都有自己的公共代码目录，查看版本信息不会涉及此目录的代码
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
    datas = git_deploy.objects.filter(platform=platform,classify=env,islog=True,usepub=True) #迁移的时候别忘记把所有的项目usepub项更新为真
    datas.update(islock=True) #全局锁
    logs=[]
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
        elif updata.method == "php":
            php_pc_release = updata.version
            php_pc_branches = updata.branch
        elif updata.method == "js":
            js_pc_release = updata.version
            js_pc_branches = updata.branch
        elif updata.method == "config":
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
        MyWeb.export_git(what='web',branch=latest_update.web_branches,reversion=latest_update.web_release) #取上个版本的web版本号
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
            MyWeb.ansible_rsync_web()
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
    #记录日志
    logdata = git_deploy_logs(name="更新",log="\r\n".join(logs),update=updata.id)
    logdata.save()
    updata.islog = True
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

