#!/usr/bin/env python
# coding:utf-8


from __future__ import absolute_import, unicode_literals
from celery import shared_task,current_task
import httplib
import dns.resolver
from time import sleep
from business.models import DomainName,DomainInfo
import socket




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

def clean_redis_obj(url,info,address='',res_code=0,alert=False):
    Bb = DomainInfo.objects.filter(name=url,new_msg=True).first()
    try:
        Bb.update_attributes(new_msg=False)
        Bb.save()
    except AttributeError:
        print 'NoneType object has no attribute update_attributes'
    print info+"OKOKOKOK"
    if address:
        address = [ str(x) for x in address]
    else:
        address = []
    Aa = DomainInfo(name=url,info=info,address=address,res_code=res_code,alert=alert)
    if Aa.is_valid():
        print "Data is storing redis-db-1 now"
        print Aa.save()
    else:
        print Aa.save()




def get_code(url,lxx):
    domain_name = url
    attribute = lxx
    jud = dns_resolver_ip(domain_name)
    # print type(jud)
    if jud:
        if set(jud) < set(attribute):
            try:
                conn = httplib.HTTPConnection(domain_name,timeout=10)
                conn.request("HEAD", "/",'',{'User-Agent' :'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
            except socket.error:
                print "limited Authority"
                info = "域名可解析但是网站没有应答"
                clean_redis_obj(domain_name,info,address=jud,alert=True)
            else:
                r1 = conn.getresponse()
                print r1.status, r1.reason
                aa = str(r1.status)[0]
                if aa == '2' or aa == '3':
                    info = "OK"
                    print "info is OK"
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=False)
                elif aa == '4':
                    print aa,"info is 客户端错误"
                    info = "客户端错误，%s,%s"% (r1.status,r1.reason)
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=True)
                elif aa == '5':
                    print aa,"info is 服务器错误"
                    info = "服务器错误，%s,%s"% (r1.status, r1.reason)
                    clean_redis_obj(domain_name,info,address=jud,res_code=r1.status,alert=True)
                else:
                    print "not 5 4 3 2"
        else:
            info = "解析IP与绑定IP不一致，域名可能被劫持"   
            no_ip = []
            for i in jud:
                if i not in attribute:
                    no_ip.appned(i)
            clean_redis_obj(domain_name,info,address=jud,no_ip=no_ip,alert=True)
    else:
        info = "域名无法解析"
        print info
        clean_redis_obj(domain_name,info,alert=True)




@shared_task()
def monitor_code(num,uuid):
    judge = 1
    while judge:
        obj = DomainName.objects.get(pk=uuid)
        attribute = obj.address.attribute
        L = attribute.split('\r\n')
        judge = obj.monitor_status
        url = obj.name
        if judge:
            # print "hello True",judge
            # dns_resolver_ip(url)
            print url
            get_code(url,L)
        else:
            print "END False %s %s"% (judge,url)
        sleep(num)
    return "END........."