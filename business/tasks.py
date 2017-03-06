#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
import httplib
import dns.resolver
from time import sleep
from business.models import DomainName,DomainInfo
import socket
import time




def dns_resolver_ip(url):
    iplist = []
    try:
        answers = dns.resolver.query(url, 'A')
    except dns.resolver.NoAnswer:
        print "Alert NoAnswer"
        return False
    else:
        for rdata in answers:
            #print url, rdata.address
            iplist.append(rdata.address)
        # print iplist
        return iplist

def clean_redis_obj(url,info,address='',no_ip='',res_code=0,alert=False):
    Bb = DomainInfo.objects.filter(name=url,new_msg=True).first()
    try:
        Bb.update_attributes(new_msg=False)
        Bb.save()
    except AttributeError:
        print 'NoneType object has no attribute update_attributes'
    # print info+"OKOKOKOK"
    if address:
        address = [ str(x) for x in address]
    else:
        address = []
    if no_ip:
        no_ip = [ str(y) for y in no_ip]
    else:
        no_ip = []
    Aa = DomainInfo(name=url,info=info,address=address,no_ip=no_ip,res_code=res_code,alert=alert)
    if Aa.is_valid():
        # print "Data is storing redis-db-1 now"
        Aa.save()
    else:
        print "%s redis存储数据失败"% url




def get_code(url,lxx):
    domain_name = url
    attribute = lxx
    jud = dns_resolver_ip(domain_name)
    # print type(jud)
    if jud:
        if set(jud) <= set(attribute):
            try:
                conn = httplib.HTTPConnection(domain_name,timeout=10)
                conn.request("HEAD", "/",'',{'User-Agent' :'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
            except socket.error:
                print "%s 域名可解析但是网站没有应答"% domain_name
                info = "域名可解析但是网站没有应答"
                clean_redis_obj(domain_name,info,address=jud,alert=True)
            else:
                r1 = conn.getresponse()
                # print r1.status, r1.reason
                aa = str(r1.status)[0]
                if aa == '2' or aa == '3':
                    info = "OK"
                    # print "info is OK"
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=False)
                elif aa == '4':
                    # print aa,"info is 客户端错误"
                    info = "客户端错误，%s,%s"% (r1.status,r1.reason)
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=True)
                elif aa == '5':
                    # print aa,"info is 服务器错误"
                    info = "服务器错误，%s,%s"% (r1.status, r1.reason)
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=True)
                else:
                    print "not 5 4 3 2"
        else:
            info = "解析IP与绑定IP不一致，域名可能被劫持"   
            no_ip = []
            for i in jud:
                if i not in attribute:
                    no_ip.append(i)
            clean_redis_obj(domain_name,info,address=jud,no_ip=no_ip,alert=True)
    else:
        info = "%s 域名无法解析" % domain_name
        print info
        clean_redis_obj(domain_name,info,alert=True)




@shared_task()
def monitor_code():
    data = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    objs = DomainName.objects.all()
    for obj in objs:
        attribute = obj.address.attribute
        L = attribute.split('\r\n')
        judge = obj.monitor_status
        url = obj.name
        if judge:
            print url
            get_code(url,L)
        else:
            print "domain %s monitor_status %s"% (url,judge)
    return "END.....task"

@shared_task()
def test_code():
    data = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print data
    print "hello"
    return "datadddddd"


