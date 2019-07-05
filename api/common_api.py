# coding:utf-8
import requests
import re
import time
import os
import shutil
from IPy import IP
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from assets.models import Server
from accounts.models import CustomUser
from django.conf import settings
from django.utils.timezone import make_aware
from datetime import datetime

import telegram
bot = telegram.Bot(token='460040810:AAG4NYR9TMwcscrxg0uXLJdsDlP3a6XohJo')

def send_message(username,text):
    chat_id = CustomUser.objects.get(username=username).mobile
    if chat_id:
        try:
            bot.sendMessage(chat_id=chat_id, text=text)
        except:
            print "用户：%s chat_id无效"% username

def check_auth(request, data): #检查用户权限的公共api函数
    if request.user.is_superuser or request.session["fun_auth"].get(data, False):
        return True
    else:
        return False

def page_list_return(total, current=1):
    min_page = current - 2 if current - 4 > 0 else 1
    max_page = min_page + 4 if min_page + 4 < total else total

    return range(min_page, max_page+1)


def pages(posts, r):
    """分页公用函数"""
    contact_list = posts
    p = paginator = Paginator(contact_list, 50)
    try:
        current_page = int(r.GET.get('page', '1'))
    except ValueError:
        current_page = 1

    page_range = page_list_return(len(p.page_range), current_page)

    try:
        contacts = paginator.page(current_page)
    except (EmptyPage, InvalidPage):
        contacts = paginator.page(paginator.num_pages)

    if current_page >= 5:
        show_first = 1
    else:
        show_first = 0
    if current_page <= (len(p.page_range) - 3):
        show_end = 1
    else:
        show_end = 0

    return contact_list, p, contacts, page_range, current_page, show_first, show_end


def sort_ip_list(ip_list):
    """ ip地址排序 """
    ip_list.sort(key=lambda s: map(int, s.split('.')))
    return ip_list


def get_mask_ip(mask):
    """ 得到一个网段所有ip """
    ips = IP(mask)
    ip_list = []
    for ip in ips:
        ip_list.append(str(ip))
    ip_list = ip_list[1:]
    return ip_list

def create_ansible_inventory(hostip_list,groupname):
    hostsFile = NamedTemporaryFile(delete=False)
    group = "[%s]" % groupname
    Lfanzheng = [group]
    for i in hostip_list:
        i = Server.objects.get(ssh_host=i)
        host = "%s ansible_ssh_port=%s ansible_ssh_use=%s ansible_ssh_pass=%s" % (i.ssh_host,i.ssh_port,i.ssh_user,i.ssh_password)
        Lfanzheng.append(host)
    for s in Lfanzheng:
        hostsFile.write(s+'\n')
    hostsFile.close()
    return hostsFile.name


def get_asset_info(asset):
    info = {'hostname': asset.ssh_host, 'ip': asset.ssh_host, 'port': int(asset.ssh_port), 'username': asset.ssh_user,'password': asset.ssh_password }


def gen_resource(ob):
    res = []
    if type(ob) == type([]):
        for asset in ob:
            info = {'hostname': asset.ssh_host, 'ip': asset.ssh_host, 'port': int(asset.ssh_port), 'username': asset.ssh_user,'password': asset.ssh_password }
            res.append(info)
    else:
        res.append({'hostname': ob.ssh_host, 'ip': ob.ssh_host, 'port': int(ob.ssh_port), 'username': ob.ssh_user,'password': ob.ssh_password })
    return res

def check_file(ifile,regx):
    f = open(ifile)
    lines = f.readlines()
    f.close()
    res = False
    for i in lines:
        if i.find(regx) == -1:
            res = False
        else:
            res = True
    return res

def get_ip_zone(ip):
    '''查找ip归属地，返回归属地名称或者空，调用:
    http://curlip.me/?db=ipip&ip=127.0.0.1
    '''
    url="http://curlip.me"
    if isValidIp(ip):
        data = {"db":"ipip","ip":ip}
        r = requests.get(url,data)
        rlist = r.text.split()
        zone = rlist[2]
        if zone == "IP": zone = "unknown"
    else:
        zone = "unknown"
    return zone

def isValidIp(ip):
    if re.match(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$', ip): return True  
    return False

def strIp_to_listIp(servers):
    servers=servers.strip()
    servers=servers.replace(","," ")
    servers=servers.replace("\r\n"," ")
    servers=servers.replace("\r"," ")
    servers_List=servers.split()
    return servers_List

def genxin_code_dir(path):
    u'''创建目录，或清空目录'''
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)
        os.makedirs(path)
    else:
        os.makedirs(path)


def add100(x):
    gg = "--exclude=" + x
    return gg

def genxin_exclude_file(files):
    if files:
        a = files.split('\r\n')
        b = ",".join(map(add100,a))
    else:
        b = ""
    return b

def utc2beijing(strtime,timeStamp=False):
    """从数据库中取出带UTC时区标志的时间对象，转换成北京时间不带时区的字符串，前端可以直接展示"""
    if not strtime:return ""
    if timeStamp:
        timestamp=int(strtime)
    else:
        try:
            pt=time.strptime(strtime,"%Y-%m-%d %H:%M:%S")
        except:
            pt=strtime.timetuple()
        timestamp = int(time.mktime(pt))
    local = timestamp+28800
    beijing = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(local))
    naive_beijing = datetime.fromtimestamp(local)
    aware_beijing = make_aware(naive_beijing)
    return beijing

def beijing2utc(strtime,timeStamp=False):
    """将不带时区标志的北京时间字符串，转换为带UTC时区标志的时间对象，保存在数据库中"""
    if not strtime:return ""
    if timeStamp:
        timestamp=int(strtime)
    else:
        pt=time.strptime(strtime,"%Y-%m-%d %H:%M:%S")
        timestamp = int(time.mktime(pt))
    local = timestamp-28800
    utc = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(local))
    naive_utc = datetime.fromtimestamp(local)
    aware_utc = make_aware(naive_utc)
    return aware_utc
