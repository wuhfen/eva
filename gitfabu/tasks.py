#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task

from api.git_api import Repo
from api.ssh_api import ssh_cmd
from api.common_api import genxin_code_dir,genxin_exclude_file,gen_resource
import time
import os
from time import sleep
import subprocess
from assets.models import Server
from api.ansible_api import MyTask, MyPlayTask
from gitfabu.models import git_deploy,my_request_task,git_coderepo,git_ops_configuration,git_website_domainname,git_deploy_logs,git_code_update

class git_moneyweb_deploy(object):
    """现金网git调用类"""
    def __init__(self,uuid,method="gengxin"):
        data = git_deploy.objects.get(pk=uuid)
        self.env = data.classify
        self.siteid = data.name
        self.uuid = uuid
        self.results = []
        try:
            server_data = git_ops_configuration.objects.get(platform=data.platform,classify=data.classify,name="源站")
            self.remoteip = server_data.remoteip
            self.remotedir = server_data.remotedir
            self.owner = server_data.owner
            self.exclude = server_data.exclude
            self.rsync_command = server_data.rsync_command
            self.last_command = server_data.last_command
        except:
            self.results.append("没有找到%s-%s-%s的源站配置,停止发布！"% (data.platform,data.classify,data.name))
            return self.results

        if self.env == "huidu":
            self.env_ch = "灰度"
        elif self.env == "online":
            self.env_ch = "生产"
        else:
            self.env_ch = "测试"

        self.base_export_dir = "/data/moneyweb/" + self.env + "/export/"
        self.merge_dir = "/data/moneyweb/" + self.env + "/merge/" + self.siteid
        self.web_dir = self.base_export_dir + self.siteid  #私有仓库检出地址
        self.php_pc_dir = self.base_export_dir + "php_pc/" #公共php代码pc端检出地址
        self.php_mobile_dir = self.base_export_dir + "php_mobile/" #公共php代码手机端检出地址
        self.js_pc_dir = self.base_export_dir + "js_pc/" #公共js代码pc端检出地址
        self.js_mobile_dir = self.base_export_dir + "js_mobile/" #公共js代码手机端检出地址

        self.now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.method = method

        if self.method == "fabu":
            self.export_git(what='web')
            self.export_git(what='php_pc')
            self.export_git(what='js_pc')
            self.export_git(what='php_mobile')
            self.export_git(what='js_mobile')
            self.merge_git()
            self.ansible_rsync_web()
            self.web_front_domain()
            self.update_release()


    def deploy_all_branch(self,what='web'):
        if what == 'web':
            repo = Repo(self.web_dir)
        elif what == 'php_pc':
            repo = Repo(self.php_pc_dir)
        elif what == 'php_mobile':
            repo = Repo(self.php_mobile_dir)
        elif what == 'js_pc':
            repo = Repo(self.js_pc_dir)
        else:
            repo = Repo(self.js_mobile_dir)
        return repo.git_all_branch()

    def branch_checkout(self,what='web',branch=None):
        if what == 'web':
            repo = Repo(self.web_dir)
        elif what == 'php_pc':
            repo = Repo(self.php_pc_dir)
        elif what == 'php_mobile':
            repo = Repo(self.php_mobile_dir)
        elif what == 'js_pc':
            repo = Repo(self.js_pc_dir)
        else:
            repo = Repo(self.js_mobile_dir)
        if branch:
            repo.git_checkout(branch)
        else:
            repo.git_checkout("master")
        repo.git_pull()
        return repo.show_commit()




    def commit_details(self,what='web',reversion=None,branch=None):
        self.web_repo = "http://fabu:DSyunweibu110110@git.dtops.cc/web/"+self.siteid+".git"
        self.js_pc_repo = "http://fabu:DSyunweibu110110@git.dtops.cc/web/1000_public_js.git"
        self.js_mobile_repo = "http://fabu:DSyunweibu110110@git.dtops.cc/web/1000m_public_js.git"
        self.php_pc_repo = "http://fabu:DSyunweibu110110@git.dtops.cc/php/1000_public_php.git"
        self.php_mobile_repo = "http://fabu:DSyunweibu110110@git.dtops.cc/php/1000m_public_php.git"
        if what == 'web':
            grepo = self.web_repo
            repo = Repo(self.web_dir)
            clone_dir = self.web_dir
        elif what == 'php_pc':
            grepo = self.php_pc_repo
            repo = Repo(self.php_pc_dir)
            clone_dir = self.php_pc_dir
        elif what == 'php_mobile':
            grepo = self.php_mobile_repo
            repo = Repo(self.php_mobile_dir)
            clone_dir = self.php_mobile_dir
        elif what == 'js_pc':
            grepo = self.js_pc_repo
            repo = Repo(self.js_pc_dir)
            clone_dir = self.js_pc_dir
        else:
            grepo = self.js_mobile_repo
            repo = Repo(self.js_mobile_dir)
            clone_dir = self.js_mobile_dir
        if branch:
            repo.git_checkout(branch)
        else:
            repo.git_checkout("master")
        repo.git_pull()
        if reversion:
            res = repo.git_log(reversion)
        else:
            res = repo.git_log(limit=1)
        return res



    def export_git(self,what='web',branch="master",reversion=None):
        data = git_deploy.objects.get(pk=self.uuid)
        try:
            private_data = git_coderepo.objects.get(platform=data.platform,classify=data.classify,title=data.name,ispublic=False)
            webuser = "//"+private_data.user+":"+private_data.passwd+"@"
            self.web_repo = webuser.join(private_data.address.split("//"))
        except:
            self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (data.platform,data.classify,data.name))
            return self.results
        try:
            php_pc_data = git_coderepo.objects.get(title="php_pc",ispublic=True)
            phpuser = "//"+php_pc_data.user+":"+php_pc_data.passwd+"@"
            self.php_pc_repo = phpuser.join(php_pc_data.address.split("//"))
        except:
            self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (data.platform,data.classify,"php_pc"))
            return self.results
        try:
            php_mobile_data = git_coderepo.objects.get(title="php_mobile",ispublic=True)
            phpuser = "//"+php_mobile_data.user+":"+php_mobile_data.passwd+"@"
            self.php_mobile_repo = phpuser.join(php_mobile_data.address.split("//"))
        except:
            self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (data.platform,data.classify,"php_mobile"))
            return self.results
        try:
            js_pc_data = git_coderepo.objects.get(title="js_pc",ispublic=True)
            jsuser = "//"+js_pc_data.user+":"+js_pc_data.passwd+"@"
            self.js_pc_repo = phpuser.join(js_pc_data.address.split("//"))
        except:
            self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (data.platform,data.classify,"js_pc"))
            return self.results
        try:
            js_mobile_data = git_coderepo.objects.get(title="js_mobile",ispublic=True)
            jsuser = "//"+js_mobile_data.user+":"+js_mobile_data.passwd+"@"
            self.js_mobile_repo = phpuser.join(js_mobile_data.address.split("//"))
        except:
            self.results.append("没有找到%s-%s-%s的git配置,停止发布！"% (data.platform,data.classify,"js_mobile"))
            return self.results

        if what == 'web':
            self.results.append("开始检出%s代码"% self.siteid)
            grepo = self.web_repo
            log_repo = private_data.address
            repo = Repo(self.web_dir)
            clone_dir = self.web_dir
            data_repo = private_data
        elif what == 'php_pc':
            self.results.append("开始检出PHP电脑端代码")
            grepo = self.php_pc_repo
            log_repo = php_pc_data.address
            repo = Repo(self.php_pc_dir)
            clone_dir = self.php_pc_dir
            data_repo =php_pc_data
        elif what == 'php_mobile':
            self.results.append("开始检出PHP手机端代码")
            grepo = self.php_mobile_repo
            log_repo = php_mobile_data.address
            repo = Repo(self.php_mobile_dir)
            clone_dir = self.php_mobile_dir
            data_repo =php_mobile_data
        elif what == 'js_pc':
            self.results.append("开始检出JS电脑端代码")
            grepo = self.js_pc_repo
            log_repo = js_pc_data.address
            repo = Repo(self.js_pc_dir)
            clone_dir = self.js_pc_dir
            data_repo =js_pc_data
        else:
            self.results.append("开始检出JS手机端代码")
            grepo = self.js_mobile_repo
            log_repo = js_mobile_data.address
            repo = Repo(self.js_mobile_dir)
            clone_dir = self.js_mobile_dir
            data_repo =js_mobile_data

        if reversion:  #如果提供了版本则拉最新代码后检出到版本
            repo.git_checkout(branch)
            repo.git_pull()
            res1 = "切换分支%s,拉取最新代码"% branch
            res2 = "切换到版本 %s"% reversion
            try:
                res = repo.git_checkout(reversion)
            except:
                os._exit(0)
            last_commit = reversion
        else:  #没有提供版本号则clone
            if data_repo.isexist == False:
                genxin_code_dir(clone_dir)
                res1 = "清空检出目录: %s"% clone_dir
                res2 = "执行git clone %s %s"% (log_repo,clone_dir)
                res = repo.git_clone(grepo,clone_dir)
                last_commit = repo.show_commit()[0]
            else:
                repo.git_checkout(branch)
                res1 = "切换到分支: %s"% branch
                res = repo.git_pull()
                res2 = "拉取最新代码"
                last_commit = repo.show_commit()[0]
        data_repo.reversion = last_commit
        data_repo.branch = branch
        data_repo.save()  #保存当前版本
        self.results.append(res1)
        self.results.append(res2)
        self.results.append("检出版本号：%s"% last_commit)
        self.results.append(res)
        return self.results

    def update_release(self):
        datas = git_deploy.objects.get(pk=self.uuid)

        private_data = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).reversion
        php_pc_data = git_coderepo.objects.get(title="php_pc",ispublic=True).reversion
        php_mobile_data = git_coderepo.objects.get(title="php_mobile",ispublic=True).reversion
        js_pc_data = git_coderepo.objects.get(title="js_pc",ispublic=True).reversion
        js_mobile_data = git_coderepo.objects.get(title="js_mobile",ispublic=True).reversion

        web_branch = git_coderepo.objects.get(platform=datas.platform,classify=datas.classify,title=datas.name,ispublic=False).branch
        php_pc_branch = git_coderepo.objects.get(title="php_pc",ispublic=True).branch
        php_mobile_branch = git_coderepo.objects.get(title="php_mobile",ispublic=True).branch
        js_pc_branch = git_coderepo.objects.get(title="js_pc",ispublic=True).branch
        js_mobile_branch = git_coderepo.objects.get(title="js_mobile",ispublic=True).branch


        last_commit = "日期：%s WEB(%s)：%s PHP电脑端(%s)：%s PHP手机端(%s)：%s JS电脑端(%s)：%s JS手机端(%s)：%s"% (self.now_time,web_branch,private_data,php_pc_branch,php_pc_data,php_mobile_branch,php_mobile_data,js_pc_branch,js_pc_data,js_mobile_branch,js_mobile_data)
        self.results.append(last_commit)
        datas.now_reversion = last_commit
        try:
            old_commits = datas.old_reversion.split('\r\n')
        except:
            old_commits = []
        old_commits.append(last_commit)
        datas.old_reversion = "\r\n".join(old_commits)
        datas.save()
        name = datas.platform+"-"+datas.classify+"-"+datas.name+"-发布"
        if self.method == "fabu":
            updata = git_code_update(name=name,code_conf=datas,web_branches=web_branch,php_pc_branches=php_pc_branch,php_mobile_branches=php_mobile_branch,js_pc_branches=js_pc_branch,
                js_mobile_branches=js_mobile_branch,web_release=private_data,php_pc_release=php_pc_data,php_moblie_release=php_mobile_data,js_pc_release=js_pc_data,js_mobile_release=js_mobile_data,memo="第一次发布",
                isaudit=True,islog=True,isuse=True)
            updata.save()
        else:
            git_code_update.objects.filter(code_conf=datas,islog=True,isuse=True).update(isuse=False)
        return self.results


    def merge_git(self):
        genxin_code_dir(self.merge_dir)  #清空或创建目录
        self.results.append("清空合并目录：%s"% self.merge_dir)
        cmd = '''\cp -ar %s/*  %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && \cp -ar %s/* %s/ && echo "代码端已合并完成" || echo "合并失败，有错误！"
            '''% (self.web_dir,self.merge_dir,self.php_pc_dir,self.merge_dir,self.php_mobile_dir,self.merge_dir,
                self.js_pc_dir,self.merge_dir,self.js_mobile_dir,self.merge_dir)
        print cmd
        self.results.append("执行语句：%s"% cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        res = p.stdout.readlines()
        resok = ",".join(res)
        print ",".join(res)
        self.results.append("执行结果：%s"% resok)
        return self.results

    def ansible_rsync_web(self):
        self.results.append("开始推送代码至服务器")
        remotedir = self.remotedir +"/"+ self.siteid
        exclude = genxin_exclude_file(self.exclude)
        for i in self.remoteip.split('\r\n'):
            self.results.append("服务器：%s,目录：%s,排除文件：%s"% (i,remotedir,exclude))
            owner = "chown -R %s %s"% (self.owner,remotedir)
            unlock = "chattr -R -i /data/wwwroot/"
            lock = "chown -R %s /data/wwwroot/%s && chattr -R +i /data/wwwroot/ && find /data/wwwroot/ -maxdepth 6 -type d -name 'Logs' | xargs -i chattr -R -i {}"% (self.owner,self.siteid)
            if self.env == 'online':
                command_unlock = ssh_cmd(i,unlock)
                self.results.append("解锁目录：%s"% unlock)
            rsync_command_res = ssh_cmd(i,self.rsync_command)  #执行推送代码前命令
            self.results.append("同步前自定义命令：%s，执行结果：%s"% (self.rsync_command,rsync_command_res))
            try:
                obj = Server.objects.get(ssh_host=i)
                task = MyTask(gen_resource(obj))
                rsync_res = task.genxin_rsync(self.merge_dir,remotedir,exclude) #将代码从CMDB本地目录推送到服务器目录，需要此机器可以公钥访问源站
                self.results.append("ansible同步代码：%s"% rsync_res)
            except:
                self.results.append("CMDB中没有此服务器信息：%s,任务失败！"% i)
                return self.results
            last_command_res = ssh_cmd(i,self.last_command)  #执行代码推送后命令
            self.results.append("同步后自定义命令：%s，执行结果：%s"% (self.last_command,last_command_res))
            if self.env == 'online':
                command_lock = ssh_cmd(i,lock)
                self.results.append("加锁目录：%s"% lock)
            else:
                command_lock = ssh_cmd(i,owner)
                self.results.append("添加属主：%s"% owner)
            return self.results

    def web_front_domain(self):
        remote_dir = "/usr/local/nginx/conf/vhost/"
        siteid = self.siteid.replace('f','')
        frontname = self.env_ch+"-"+self.siteid+"前端域名"
        agname = self.env_ch+"-"+self.siteid+"AG域名"
        backendname = self.env_ch+"-"+self.siteid+"后台域名"
        front_data = git_deploy.objects.get(pk=self.uuid).deploy_domain.get(name=frontname)
        if self.env == "huidu" or self.env == "online":
            ag_data = git_deploy.objects.get(pk=self.uuid).deploy_domain.get(name=agname)
            backend_data = git_deploy.objects.get(pk=self.uuid).deploy_domain.get(name=backendname)
        self.results.append("开始域名配置")
        try:
            front_remoteips = git_ops_configuration.objects.get(platform="现金网",classify=self.env,name="源站").remoteip
        except:
            self.results.append("ERROR:现金网-%s-源站没有配置"% self.env)
        if self.env == "huidu" or self.env == "online": #测试环境不需要ag与后台
            try:
                ag_remoteips = git_ops_configuration.objects.get(platform="现金网",classify=self.env,name="AG").remoteip
            except:
                self.results.append("ERROR:现金网-%s-AG没有配置"% self.env)
            try:
                backend_remoteips = git_ops_configuration.objects.get(platform="现金网",classify=self.env,name="后台").remoteip
            except:
                self.results.append("ERROR:现金网-%s-后台没有配置"% self.env)
        #同步前端域名
        if "f" in self.siteid:
            local_nginx_file = "front_fu.conf"
        else:
            local_nginx_file = "front_zhu.conf"
        try:
            resource = gen_resource([Server.objects.get(ssh_host=i) for i in front_remoteips.split('\r\n')])
            playtask = MyPlayTask(resource)
            res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,front_data.conf_file_name,siteid,front_data.domainname)
            self.results.append("源站：%s 文件名：%s"% (front_remoteips,remote_dir+front_data.conf_file_name))
            self.results.append("域名：%s"% front_data.domainname)
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
        if self.env == "huidu" or self.env == "online":
            if self.env == "huidu":
                local_nginx_file = "agent_huidu.conf"
            elif self.env == "online":
                local_nginx_file = "agent.conf"
            else:
                pass #测试环境不配置域名
            try:
                resource = gen_resource([Server.objects.get(ssh_host=i) for i in ag_remoteips.split('\r\n')])
                playtask = MyPlayTask(resource)
                res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,ag_data.conf_file_name,self.siteid,ag_data.domainname)
                self.results.append("AG站：%s 文件名：%s"% (ag_remoteips,remote_dir+ag_data.conf_file_name))
                self.results.append("域名：%s"% ag_data.domainname)
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
            local_nginx_file = "backend.conf"
            try:
                resource = gen_resource([Server.objects.get(ssh_host=i) for i in backend_remoteips.split('\r\n')])
                playtask = MyPlayTask(resource)
                res = playtask.rsync_nginx_conf(local_nginx_file,remote_dir,backend_data.conf_file_name,siteid,backend_data.domainname)
                self.results.append("后台站：%s 文件名：%s"% (backend_remoteips,remote_dir+backend_data.conf_file_name))
                self.results.append("域名：%s"% backend_data.domainname)
                if res == 0:
                    self.results.append("结果：成功！")
                elif res == 1:
                    self.results.append("结果：执行错误！")
                else:
                    self.results.append("结果：主机不可用！")
            except:
                self.results.append("配置后台域名失败，任务结束！")
                return self.results
        #同步源站反代域名
        if self.env == "huidu":
            local_nginx_file = "front_proxy.conf"
            remote_nginx_file = self.siteid+".s1119.conf"
            try:
                proxy_remoteips = git_ops_configuration.objects.get(platform="现金网",classify=self.env,name="源站反代").remoteip
                resource = gen_resource([Server.objects.get(ssh_host=i) for i in proxy_remoteips.split('\r\n')])
                playtask = MyPlayTask(resource)
                playtask.rsync_nginx_conf(local_nginx_file,remote_dir,remote_nginx_file,siteid,front_data.domainname)
                self.results.append("源站反代站：%s 文件名：%s"% (proxy_remoteips,remote_dir+remote_nginx_file))
                self.results.append("域名：%s"% front_data.domainname)
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

    if data.platform == "现金网":
        #判断锁文件，有则等待，无则创建并发布，发布完成后删除锁文件
        lock_file = "/tmp/"+data.classify+"_moneyweb.lock"
        while os.path.isfile(lock_file):
            sleep(1)
            print "等待1秒"
        fo = open(lock_file,"wb")
        fo.write("locked")
        fo.close
        logs.append("创建锁文件：%s"% lock_file)
        MyWeb = git_moneyweb_deploy(uuid,method="fabu")
        logs = logs+MyWeb.results
        os.remove(lock_file)
        logs.append("删除锁文件：%s"% lock_file)

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
    data.islog = True
    data.save()
    return "celery FABU task is end"


@shared_task()
def git_update_task(uuid,myid):
    updata = git_code_update.objects.get(pk=uuid)
    data = updata.code_conf
    logs=[]
    start = "%s-%s环境-%s-%s更新"% (data.platform,data.classify,data.name,updata.method)
    logs.append(start)
    print start
    if data.platform == "现金网":
        #判断锁文件，有则等待，无则创建，更新完成后删除锁文件
        lock_file = "/tmp/"+data.classify+"_moneyweb.lock"
        while os.path.isfile(lock_file):
            sleep(1)
            print "等待1秒"
        fo = open(lock_file,"wb")
        fo.write("locked")
        fo.close
        logs.append("创建锁文件：%s"% lock_file)
        #开始更新
        MyWeb = git_moneyweb_deploy(data.id)
        if updata.method == 'web':
            print "分支%s,版本号%s"% (updata.web_branches,updata.web_release)
            MyWeb.export_git(what='web',branch=updata.web_branches,reversion=updata.web_release)
        MyWeb.export_git(what='php_pc',branch=updata.php_pc_branches,reversion=updata.php_pc_release)
        MyWeb.export_git(what='js_pc',branch=updata.js_pc_branches,reversion=updata.js_pc_release)
        MyWeb.export_git(what='php_mobile',branch=updata.php_mobile_branches,reversion=updata.php_moblie_release)
        MyWeb.export_git(what='js_mobile',branch=updata.js_mobile_branches,reversion=updata.js_mobile_release)
        MyWeb.merge_git()
        MyWeb.ansible_rsync_web()
        MyWeb.update_release()
        if updata.method == "php_pc":
            release = updata.php_pc_release
            branches = updata.php_pc_branches
            res = MyWeb.commit_details(what='php_pc',reversion=release,branch=branches)
        elif updata.method == "js_pc":
            release = updata.js_pc_release
            branches = updata.js_pc_branches
            res = MyWeb.commit_details(what='js_pc',reversion=release,branch=branches)
        elif updata.method == "php_mobile":
            release = updata.php_moblie_release
            branches = updata.php_mobile_branches
            res = MyWeb.commit_details(what='php_mobile',reversion=release,branch=branches)
        elif updata.method == "js_mobile":
            release = updata.js_mobile_release
            branches = updata.js_mobile_branches
            res = MyWeb.commit_details(what='js_mobile',reversion=release,branch=branches)
        else:
            release = updata.web_release
            branches = updata.web_branches
            res = MyWeb.commit_details(what='web',reversion=release,branch=branches)
        #更新结束
        logs = logs+MyWeb.results
        os.remove(lock_file)
        logs.append("删除锁文件：%s"% lock_file)
    print "已完成%s"% updata.name
    logs.append("已完成%s"% updata.name)
    #更新任务isend
    mydata = my_request_task.objects.get(pk=myid)
    mydata.status = "已完成"
    mydata.isend = True
    mydata.save()
    #记录日志
    logdata = git_deploy_logs(name="更新",log="\r\n".join(logs),git_deploy=data,update=updata.id)
    logdata.save()
    #标记当前使用版本
    updata.islog = True
    updata.isuse = True
    updata.details = res
    updata.save()
    return "celery GENGXIN task is end"

@shared_task()
def git_update_public_task(uuid,myid):
    updata = git_code_update.objects.get(pk=uuid)
    if "huidu" in updata.name:
        env = "huidu"
    elif "online" in updata.name:
        env = "online"
    else:
        env = "test"
    datas = git_deploy.objects.filter(platform="现金网",classify=env,islog=True)
    logs=[]
    #判断锁文件，有则等待，无则创建，更新完成后删除锁文件
    lock_file = "/tmp/"+env+"_moneyweb.lock"
    while os.path.isfile(lock_file):
        sleep(1)
        print "等待1秒"
    fo = open(lock_file,"wb")
    fo.write("locked")
    fo.close
    logs.append("创建锁文件：%s"% lock_file)

    for data in datas:
        start = "现金网-%s环境-%s-%s更新"% (env,data.name,updata.method)
        logs.append(start)
        print start
        latest_update = data.deploy_update.get(islog=True,isuse=True) #获取上一个版本实例
        php_pc_release = latest_update.php_pc_release
        php_moblie_release = latest_update.php_moblie_release
        js_pc_release = latest_update.js_pc_release
        js_mobile_release = latest_update.js_mobile_release
        php_pc_branches = latest_update.php_pc_branches
        php_mobile_branches = latest_update.php_mobile_branches
        js_pc_branches = latest_update.js_pc_branches
        js_mobile_branches = latest_update.js_mobile_branches
        #开始更新
        MyWeb = git_moneyweb_deploy(data.id)
        if updata.method == "php_pc":
            php_pc_release = updata.php_pc_release
            php_pc_branches = updata.php_pc_branches
        elif updata.method == "js_pc":
            js_pc_release = updata.js_pc_release
            js_pc_branches = updata.js_pc_branches
        elif updata.method == "php_mobile":
            php_moblie_release = updata.php_moblie_release
            php_mobile_branches = updata.php_mobile_branches
        elif updata.method == "js_mobile":
            js_mobile_release = updata.js_mobile_release
            js_mobile_branches = updata.js_mobile_branches
        else:
            pass
        MyWeb.export_git(what='php_pc',branch=php_pc_branches,reversion=php_pc_release)
        MyWeb.export_git(what='js_pc',branch=js_pc_branches,reversion=js_pc_release)
        MyWeb.export_git(what='php_mobile',branch=php_mobile_branches,reversion=php_moblie_release)
        MyWeb.export_git(what='js_mobile',branch=js_mobile_branches,reversion=js_mobile_release)
        MyWeb.merge_git()
        MyWeb.ansible_rsync_web()
        MyWeb.update_release()
        #更新结束
        logs = logs+MyWeb.results
        new_data = git_code_update(name=updata.name,code_conf=data,method=updata.method,web_release=latest_update.web_release,
            php_pc_release=php_pc_release,js_pc_release=js_pc_release,php_moblie_release=php_moblie_release,js_mobile_release=js_mobile_release,
            web_branches=latest_update.web_branches,php_pc_branches=php_pc_branches,php_mobile_branches=php_mobile_branches,js_pc_branches=js_pc_branches,
            js_mobile_branches=js_mobile_branches,memo=updata.memo,isaudit=True,islog=True,isuse=True)
        new_data.save()
    if updata.method == "php_pc":
        release = updata.php_pc_release
        branches = updata.php_pc_branches
        res = MyWeb.commit_details(what='php_pc',reversion=release,branch=branches)
    elif updata.method == "js_pc":
        release = updata.js_pc_release
        branches = updata.js_pc_branches
        res = MyWeb.commit_details(what='js_pc',reversion=release,branch=branches)
    elif updata.method == "php_mobile":
        release = updata.php_moblie_release
        branches = updata.php_mobile_branches
        res = MyWeb.commit_details(what='php_mobile',reversion=release,branch=branches)
    elif updata.method == "js_mobile":
        release = updata.js_mobile_release
        branches = updata.js_mobile_branches
        res = MyWeb.commit_details(what='js_mobile',reversion=release,branch=branches)
    else:
        release = updata.web_release
        branches = updata.web_branches
        res = MyWeb.commit_details(what='web',reversion=release,branch=branches)
    os.remove(lock_file)
    logs.append("删除锁文件：%s"% lock_file)
    print "已完成%s"% updata.name
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
    updata.details = res
    updata.save()
    return "celery GENGXIN-PUBLIC task is end"

@shared_task()
def commit_details_task(uuid,env=None):
    updata = git_code_update.objects.get(pk=uuid)
    data = updata.code_conf
    if data:
        MyWeb = git_moneyweb_deploy(data.id)
    else:
        MyWeb = git_moneyweb_deploy(git_deploy.objects.filter(platform="现金网",classify=env,islog=True)[0].id)
    if updata.method == "php_pc":
        release = updata.php_pc_release
        branches = updata.php_pc_branches
        res = MyWeb.commit_details(what='php_pc',reversion=release,branch=branches)
    elif updata.method == "js_pc":
        release = updata.js_pc_release
        branches = updata.js_pc_branches
        res = MyWeb.commit_details(what='js_pc',reversion=release,branch=branches)
    elif updata.method == "php_mobile":
        release = updata.php_moblie_release
        branches = updata.php_mobile_branches
        res = MyWeb.commit_details(what='php_mobile',reversion=release,branch=branches)
    elif updata.method == "js_mobile":
        release = updata.js_mobile_release
        branches = updata.js_mobile_branches
        res = MyWeb.commit_details(what='js_mobile',reversion=release,branch=branches)
    else:
        release = updata.web_release
        branches = updata.web_branches
        res = MyWeb.commit_details(what='web',reversion=release,branch=branches)
    updata.details = res
    updata.save()
