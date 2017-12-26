#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from assets.forms import RAMForm,AssetForm,NICForm
from assets.models import Asset, NIC
from django.contrib.auth.decorators import login_required
import time
from assets.system_opt.init_system import init_sys
import telegram
import json
from api.ssh_api import ssh_cmd
from gitfabu.tasks import git_fabu_task,git_moneyweb_deploy,git_update_task,git_update_public_task
from gitfabu.models import git_code_update
global bot
#bot = telegram.Bot(token='460040810:AAG4NYR9TMwcscrxg0uXLJdsDlP3a6XohJo')
bot = telegram.Bot(token='480303523:AAHjlmvdiEBZZ_zs78cj3hivwzcpyJuz8xQ')

# Create your views here.
from assets.models import Server
from gitfabu.models import git_task_audit
from accounts.models import CustomUser

from api.common_api import isValidIp
def helpp(message):
    text = ('/help - 查看帮助\n'
            '/shell - 执行shell命令，格式: host@command\n'
            '/get_mytask - 不带id查看审核任务列表(最近10个)，带id查看详情\n'
            '/get_mytask_all - 查看所有的审核任务\n'
            '/audit - 审核任务，格式：task_id@yes/no/go，go是强制通过\n'
            '/ba - 批量审核任务，格式：yes/no/go@task_id1 task_id2 ...\n'
            '/get_host - 获取主机信息，格式：IP')
    bot.sendMessage(chat_id=message.chat.id, text=text)

def shell(message):
    try:
        ip = message.text.split()[1].split('@')[0]
        cmd = message.text.split('@')[-1]
        if not isValidIp(ip):
            text = "IP格式错误"
            bot.sendMessage(chat_id=message.chat.id, text=text)
            return 9
    except IndexError:
        text = "缺少参数！/shell IP地址@命令"
        bot.sendMessage(chat_id=message.chat.id, text=text)
        return 9
    path = "[root@localhost ~]# "
    try:
        Server.objects.get(ssh_host=ip)
    except:
        text = "此IP：%s 不在CMDB记录中"% ip
        bot.sendMessage(chat_id=message.chat.id, text=text)
        return 8
    try:
        res = ssh_cmd(ip,cmd)
        print res
        res = "  ".join(res)
        text = path+'\r\n'+res
    except:
        text = "连接超时！"
    num = len(text)/4096
    if num == 0:
        bot.sendMessage(chat_id=message.chat.id, text=text)
    else:
        start = 0
        for i in num:
            end = start + 4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])
            start += 4096
        if len(text)%4096 == 0:
            pass
        else:
            end = start + len(text)%4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])




    # bot.sendMessage(chat_id=message.chat.id, text=text)

def get_host(message):
    try:
        ip = message.text.split()[1]
        if not isValidIp(ip):
            text = "IP：%s 格式错误"% ip
            bot.sendMessage(chat_id=message.chat.id, text=text)
            return 9
    except IndexError:
        text = "缺少参数！/get_host IP地址"
        bot.sendMessage(chat_id=message.chat.id, text=text)
        return 9

    try:
        server = Server.objects.get(ssh_host=ip)
        text = 'IP: %s \nUSER: %s \nPORT: %s \n PASSWD: %s \n'% (ip,server.ssh_user,server.ssh_port,server.ssh_password)
    except:
        text = "此IP不在CMDB记录中"
    bot.sendMessage(chat_id=message.chat.id, text=text)

def get_mytask(message):
    text = []
    tuser = message.chat.first_name
    username = CustomUser.objects.get(first_name=tuser)
    args = message.text.split()
    if len(args) > 2:
        text.append("格式错误！/get_mytask 或者 /get_mytask id")
    elif len(args) == 2:
        try:
            data = git_task_audit.objects.get(id=args[-1])
            text.append("ID: "+str(data.id)+'\n'+"标题："+data.request_task.name+'\n'+"状态："+data.request_task.status+'\n'+"描述："+data.request_task.memo+'\n'+"申请人："+data.request_task.initiator.username+'\n')
            for i in data.request_task.reqt.all():
                if i.isaudit:
                    if i.ispass:
                        text.append("审核人： "+i.auditor.username+"已通过\n")
                    else:
                        text.append("审核人： "+i.auditor.username+"未通过\n")
                else:
                    text.append("审核人： "+i.auditor.username+"未审核\n")
            if data.request_task.table_name == "git_deploy":
                print "发布任务"
                df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
                f_dname = "生产-%s前端域名"% df.name
                domain = df.deploy_domain.get(name=f_dname).domainname.split()[0:5]
                text.append("域名："+"\n".join(domain))
            else:
                print "更新任务"
                bf = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
                df = bf.code_conf
                f_dname = "生产-%s前端域名"% df.name
                print df.deploy_domain.get(name=f_dname).domainname
                domain = df.deploy_domain.get(name=f_dname).domainname.split()[0:5]
                text.append("域名: http://")
                text.append(" ".join(domain))
        except:
            text.append("没有找到此ID：%s 信息"% args[-1])
    else:
        if "get_mytask_all" in message.text:
            data = git_task_audit.objects.filter(auditor=username,loss_efficacy=False)
        else:
            data = git_task_audit.objects.filter(auditor=username,loss_efficacy=False)[:10]
        if data:
            for i in data:
                if i.isaudit:
                    stats = "已审核"
                    if i.ispass:
                        status = "已通过"
                    else:
                        status = "未通过"
                    text.append("ID: "+str(i.id)+"-->"+i.request_task.name+"-->"+stats+"-->"+status+'\n')
                else:
                    stats = "未审核"
                    text.append("ID: "+str(i.id)+"-->"+i.request_task.name+"-->"+stats+'\n')
        else:
            text.append("还没有审核任务！")
    text = "".join(text)
    num = len(text)/4096
    if num == 0:
        bot.sendMessage(chat_id=message.chat.id, text=text)
    else:
        start = 0
        for i in num:
            end = start + 4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])
            start += 4096
        if len(text)%4096 == 0:
            pass
        else:
            end = start + len(text)%4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])

def audit(message):
    tuser = message.chat.first_name
    username = CustomUser.objects.get(first_name=tuser)
    try:
        uuid = message.text.split()[1].split('@')[0]
        ispass = message.text.split()[1].split('@')[1]
    except IndexError:
        text = "缺少参数！/audit 任务ID@yes or no"
        bot.sendMessage(chat_id=message.chat.id, text=text)
        return 9

    if ispass == "yes" or ispass == "(yes)" or ispass == "Yes" or ispass == "YES":
        ok = True
        go = False
        postil = "%s 使用telegram通过了任务ID: %s"% (username,uuid)
    elif ispass == "no" or ispass == "(no)" or ispass == "No" or ispass == "NO":
        ok = False
        go = False
        postil = "%s 使用telegram否决了任务ID: %s"% (username,uuid)
    elif ispass == "go":
        ok = True
        go = True
        postil = "%s 使用telegram强制通过了任务ID: %s"% (username,uuid)
    else:
        bot.sendMessage(chat_id=message.chat.id, text="格式错误！/audit 任务ID@yes or no")
        return 9
    try:
        data = git_task_audit.objects.get(id=uuid)
        df = eval(data.request_task.table_name).objects.get(pk=data.request_task.uuid)
        if go:
            for i in data.request_task.reqt.all():
                i.ispass = ok
                i.isaudit = True
                i.postil = postil
                i.save()
        else:
            data.ispass = ok
            data.isaudit = True
            data.postil = postil
            data.save()
        if not ok:
            bot.sendMessage(chat_id=message.chat.id, text=postil)
            return 2
        alldata = data.request_task.reqt.all()
        if False not in [i.ispass for i in alldata]:
            data.request_task.status="通过审核，更新中"
            data.request_task.save()
            df.isaudit= True
            df.save()
            if data.request_task.table_name == "git_deploy":
                text = postil + "开始现金网发布"
                name = "发布"
                reslut = git_fabu_task.delay(data.request_task.uuid,data.request_task.id)
            else:
                name = "更新"
                if df.code_conf:
                    text = postil+"开始现金网更新"
                    reslut = git_update_task.delay(data.request_task.uuid,data.request_task.id)
                else:
                    if "现金网" in df.name: platform="现金网"
                    if "蛮牛" in df.name: platform="蛮牛"
                    reslut = git_update_public_task.delay(data.request_task.uuid,data.request_task.id,platform=platform)
                    text = postil + df.name
            bot.sendMessage(chat_id=message.chat.id, text=text)
            try:
                reslut.wait(timeout=600)
            except:
                bot.sendMessage(chat_id=message.chat.id, text="ID: %s 任务超时，可能失败了！"% uuid)
                return 7
            if reslut.successful():
                deploy_data = df.code_conf
                dflog = deploy_data.deploy_logs.filter(name=name,update=df.id)
                for i in dflog:
                    text = "".join(i.log)
        else:
            text="你已审核，等待其他人审核！"
    except:
        text="没有找到此任务，ID：%s"% uuid
    num = len(text)/4096
    if num == 0:
        bot.sendMessage(chat_id=message.chat.id, text=text)
    else:
        start = 0
        for i in num:
            end = start + 4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])
            start += 4096
        if len(text)%4096 == 0:
            pass
        else:
            end = start + len(text)%4096
            bot.sendMessage(chat_id=message.chat.id, text=text[start:end])


def handle_message(message):
    text = message.text
    tuser = message.chat.first_name
    try:
        username = CustomUser.objects.get(first_name=tuser)
    except:
        bot.sendMessage(chat_id=message.chat.id, text="未认证用户！请联系murphy")
        return 4
    try:
        if '/shell' in text:
            shell(message)
        elif '/get_mytask' in text:
            get_mytask(message)
        elif '/help' in text:
            helpp(message)
        elif '/audit' in text:
            audit(message)
        elif '/get_host' in text:
            get_host(message)
        else:
            bot.sendMessage(chat_id=message.chat.id, text="无效命令，输入 /help 获取帮助")
    except TypeError:
        pass



@login_required()
def index(request):
    return render(request,'default/index.html',locals())

def auth_error(request):
    return render(request,'default/error_auth.html',locals())

def success(request):
    return render(request,'default/success.html',locals())

def test(request):
    data = "Hello World!"
    bb = init_sys("154")
    bb.set_selinux()
    return render(request,'default/test233.html',locals())

@csrf_exempt
def hello(request):
    if request.method == "POST":

        update = telegram.Update.de_json(json.loads(request.body),bot)
        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text
            print "user-id:%s,内容：%s"% (chat_id,text)
            handle_message(update.message)
        return HttpResponse("OK")
    return HttpResponse("OK")