#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import urllib2
import sys
import logging
#from pyzabbix import ZabbixAPI

class zabbixtools(object):
    def __init__(self,url,username,password):
        self.url = url.rstrip('/') + '/api_jsonrpc.php'
        self.header = {
            "Content-Type": "application/json-rpc",
            'User-Agent': 'python/pyzabbix',
            'Cache-Control': 'no-cache'
        }
        self.username = username
        self.password = password
        self.authID = self.user_login()

    def user_login(self):
        aa = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "Admin",
                "password": "JRFnuwVXM45E.ds"
                },
            "id": 0
            }
        data = json.dumps(aa)
        request = urllib2.Request(self.url,data)
        for key in self.header:
            request.add_header(key,self.header[key])
        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            print "Auth Failed, Please Check Your Name And Password:",e.code
        else:
            response = json.loads(result.read())
            result.close()
            authID = response['result']
            print authID
            return authID

    def get_data(self,data,hostip=""):
        request = urllib2.Request(self.url,data)
        for key in self.header:
            request.add_header(key,self.header[key])
        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            elif hasattr(e, 'code'):
                print 'The server could not fulfill the request.'
                print 'Error code: ', e.code
            return 0
        else:
            response = json.loads(result.read())
            result.close()
            return response


    def host_get(self,hostip):     ##获取某个主机的名称，id，提供ip
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output":["hostid","name","status","host"],
                "filter": {"host": [hostip]}
                },
            "auth": self.authID,
            "id": 1
            })

        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            host = res[0]
            print host['hostid']
            return host['hostid']
            # if host['status'] == '1':
            #     print "\t","\033[1;31;40m%s\033[0m" % "Host_IP:","\033[1;31;40m%s\033[0m" % host['host'].ljust(15),'\t',"\033[1;31;40m%s\033[0m" % "Host_Name:","\033[1;31;40m%s\033[0m" % host['name'].encode('GBK'),'\t',"\033[1;31;40m%s\033[0m" % u'未在监控状态'.encode('GBK')
            #     return host['hostid']
            # elif host['status'] == '0':
            #     print "\t","\033[1;32;40m%s\033[0m" % "Host_IP:","\033[1;32;40m%s\033[0m" % host['ip'].ljust(15),'\t',"\033[1;32;40m%s\033[0m" % "Host_Name:","\033[1;32;40m%s\033[0m" % host['name'].encode('GBK'),'\t',"\033[1;32;40m%s\033[0m" % u'在监控状态'.encode('GBK')
            #     return host['hostid']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "Get Host Error or cannot find this host,please check !"
            return 0

    def show_host(self):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output":["status","host"],
                },
            "auth": self.authID,
            "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            nlist = [i['host'] for i in res if i['status'] == '0']
            unlist = [i['host'] for i in res if i['status'] == '1']
            count = int(len(nlist)) + int(len(unlist))
            if nlist: print "\t","\033[1;32;40m%s\033[0m" % u"当前共有 %s 个主机\r\n" % count,'\t',"\033[1;32;40m%s\033[0m" % u"已监控主机：%s" % json.dumps(nlist, encoding="UTF-8", ensure_ascii=False)
            if unlist: print '\t',"\033[1;32;40m%s\033[0m" % u"未监控主机：%s" % json.dumps(unlist, encoding="UTF-8", ensure_ascii=False)

    def host_create(self,hostip,hostname,hostport,hostgroup):
        hostid = self.host_get(hostip)

        groupid = self.group_get(hostgroup)
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": hostip,
                "name": hostname,

                "interfaces": [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": hostip,
                        "dns": "",
                        "port": hostport
                    }
                ],
                "groups": [
                    {
                        "groupid": groupid
                    }
                ],
                "inventory_mode": 0,
            },
            "auth": self.authID,
            "id": 1
            })
        if hostid == 0:
            res = self.get_data(data)['result']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "This host aleady exists in zabbix!"
            res = 0

        print res
        return res

    def host_delete(self,hostip):
        hostid = host_get(hostip)
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.delete",
            "params": [hostid],
            "auth": self.authID,
            "id": 1
            })
        if hostid == 0:
            return 0
        else:
            res = self.get_data(data)['result']
            print res['hostids']
            print "This host %s is delete success" % hostip
            return res['hostids']


    def group_get(self,groupname):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "name": [groupname]
                    }
                },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):

            print res[0]['groupid']
            return res[0]['groupid']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "Cannot find this group in zabbix!"
            return 0


    def group_create(self,groupname):
        groupid = self.group_get(groupname)
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.create",
                "params": {
                    "name": groupname
                },
                "auth": self.authID,
                "id": 1
            })
        if groupid == 0:
            res = self.get_data(data)['result']
            print res[0]['groupid']
            return res[0]['groupid']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "This group aleady exists in zabbix!"
            return 0

    def group_info(self,groupname):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": "extend",
                    "selectHosts": ['host'],
                    "selectTemplates": ['name'],
                    "filter": {"name": [groupname]}
                    },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            temps = res[0]['templates']
            hosts = res[0]['hosts']
            print "\t","\033[1;32;40m%s\033[0m" % "Group:","\033[1;32;40m%s\033[0m" % groupname
            tlist = [t['name'] for t in temps]
            hlist = [h['host'] for h in hosts]
            if tlist:
                print "\t","\033[1;32;40m%s\033[0m" % u"组内模板有: ","\033[1;32;40m%s\033[0m" % json.dumps(tlist, encoding="UTF-8", ensure_ascii=False)
            if hlist:
                print "\t","\033[1;32;40m%s\033[0m" % u"组内主机有: ","\033[1;32;40m%s\033[0m" % json.dumps(hlist, encoding="UTF-8", ensure_ascii=False)
        else:
            print "\t","\033[1;31;40m%s\033[0m" % u"Cannot find this group in zabbix: "
            return 0

    def show_group(self):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": ['name']
                    },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        print res
        nlist = [i['name'] for i in res]
        if nlist: print "\t","\033[1;32;40m%s\033[0m" % u"当前共有 %s 个组\r\n" % len(nlist),'\t',"\033[1;32;40m%s\033[0m" % u"组名：%s" % json.dumps(nlist, encoding="UTF-8", ensure_ascii=False)

    def group_delete(self,groupname):
        groupid = self.group_get(groupname)
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.delete",
                "params": [groupid],
                "auth": self.authID,
                "id": 1
            })
        if groupid == 0:
            return 0
        else:
            res = self.get_data(data)['result']
            print res['groupids']
            print "This group %s is delete success" % groupname
            return res['groupids']

    def template_get(self,templatename):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "template.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "host": [templatename]
                    }
                },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):

            print res[0]['templateid']
            return res[0]['templateid']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "Cannot find this Template in zabbix!"
            return 0

    def list_output(self,gglist,number):
        a = 0
        b = number
        num = len(gglist)/number
        for i in range(num):
            print '\t\t',"\033[1;32;40m%s\033[0m" % json.dumps(gglist[a:b], encoding="UTF-8", ensure_ascii=False)
            a += number
            b += number

    def template_info(self,templatename):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "template.get",
                "params": {
                    "output": "extend",
                    "selectHosts": ['host'],
                    "selectItems": ['name','key_','delay','status'],
                    "selectDiscoveries": ['delay','name','key_','status'],
                    "selectTriggers": ['status','description','expression','value'],
                    "filter": {
                        "host": [templatename]
                    }
                },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        print '\t',"\033[1;35;40m%s\033[0m" % u"模板：%s" % templatename
        try:
            hosts = res[0]['hosts']
        except KeyError:
            hosts = ''
        hlist = [i['host'] for i in hosts if hosts]
        print '\t',"\033[1;35;40m%s\033[0m" % u"关联此模板的主机："
        self.list_output(hlist,8)
        try:
            discoveries = res[0]['discoveries']
        except KeyError:
            discoveries = ''
        if discoveries:
            print '\t',"\033[1;35;40m%s\033[0m" % u"自动发现规则："
            for i in discoveries:
                if i['status'] == '0':
                    print '\t',"\033[1;32;40m%s\033[0m" % u"模板自动发现规则：%s" % i['name'],'\t',"\033[1;32;40m%s\033[0m" % u"规则执行周期：%s 秒" % i['delay'],'\t',"\033[1;32;40m%s\033[0m" % u"已启用"
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % u"模板自动发现规则：%s" % i['name'],'\t',"\033[1;32;40m%s\033[0m" % u"规则执行周期：%s 秒" % i['delay'],'\t',"\033[1;32;40m%s\033[0m" % u"未启用"
        try:
            items = res[0]['items']
        except KeyError:
            items = ''
        if items:
            print '\t',"\033[1;35;40m%s\033[0m" % u"监控项："
            for i in items:
                if i['status'] == '0':
                    print '\t',"\033[1;32;40m%s\033[0m" % u"监控项名称：%s" % i['name'],'\t',"\033[1;32;40m%s\033[0m" % u"监控项KEY：%s" % i['key_'],'\t',"\033[1;32;40m%s\033[0m" % u"数据收集周期：%s 秒" % i['delay'],'\t',"\033[1;32;40m%s\033[0m" % u"已启用"
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % u"监控项名称：%s" % i['name'],'\t',"\033[1;32;40m%s\033[0m" % u"监控项KEY：%s" % i['key_'],'\t',"\033[1;32;40m%s\033[0m" % u"数据收集周期：%s 秒" % i['delay'],'\t',"\033[1;32;40m%s\033[0m" % u"未启用"
        try:
            triggers = res[0]['triggers']
        except KeyError:
            triggers = ''
        if triggers:
            print '\t',"\033[1;35;40m%s\033[0m" % u"告警触发器："
            for i in triggers:
                if i['status'] == '0':
                    print '\t',"\033[1;32;40m%s\033[0m" % u"触发器名称：%s" % i['description'],'\t',"\033[1;32;40m%s\033[0m" % u"表达式：%s" % i['expression'],'\t',"\033[1;32;40m%s\033[0m" % u"已启用"
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % u"触发器名称：%s" % i['description'],'\t',"\033[1;32;40m%s\033[0m" % u"表达式：%s" % i['expression'],'\t',"\033[1;32;40m%s\033[0m" % u"未启用"



    def select_info(self,key):
        hdata = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output":["name","status","host"],
                "search": {'host': key},
                },
            "auth": self.authID,
            "id": 1
            })
        gdata = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output":["name"],
                "search": {'name':key},
                },
            "auth": self.authID,
            "id": 1
            })
        tdata = json.dumps({
            "jsonrpc": "2.0",
            "method": "template.get",
            "params": {
                "output":["host"],
                "search": {'host':key},
                },
            "auth": self.authID,
            "id": 1
            })
        idata = json.dumps({
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output":["name"],
                "search": {'name':key},
                },
            "auth": self.authID,
            "id": 1
            })
        request = [hdata,gdata,tdata,idata]
        result_list = []
        for i in request:
            res = self.get_data(i)['result']
            if (res != 0) and (len(res) !=0 ):
                for i in res[0]:
                    try:
                        if i['hostid']:
                            print '\t',"\033[1;35;40m%s\033[0m" % u"找到主机 %"% i['host']
                    except TypeError:
                        pass
                    try:
                        if i['groupid']:
                            print '\t',"\033[1;35;40m%s\033[0m" % u"找到组 %"% i['name']
                    except TypeError:
                        pass
                    try:
                        if i['templateid']:
                            print '\t',"\033[1;35;40m%s\033[0m" % u"找到模板 %"% i['host']
                    except TypeError:
                        pass
                    try:
                        if i['itemid']:
                            print '\t',"\033[1;35;40m%s\033[0m" % u"找到监控项 %"% i['name']
                    except TypeError:
                        pass




        # res = self.get_data(hdata)['result']
        # if (res != 0) and (len(res) !=0 ):
        #     print res





    def show_template(self):
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "template.get",
                "params": {
                    "output": ['name'],
                },
                "auth": self.authID,
                "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            nlist = [i['name'] for i in res]
            if nlist: print "\t","\033[1;32;40m%s\033[0m" % u"当前共有 %s 个模板\r\n" % len(nlist),'\t',"\033[1;32;40m%s\033[0m" % u"模板名：%s" % json.dumps(nlist, encoding="UTF-8", ensure_ascii=False)

    def template_delete(self,templatename):
        template_id = self.template_get(templatename) 
        if template_id:
            data = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "template.delete",
                    "params": [template_id],
                    "auth": self.authID,
                    "id": 1
                })
            res = self.get_data(data)['result']
            print "\t","\033[1;35;40m%s\033[0m" % u"模板 %s 已删除！" % templatename
        else:
            print "\t","\033[1;31;40m%s\033[0m" % u"模板 %s 删除失败！" % templatename
            return 0



    def host_add_groups(self,hostip,grouplist):
        hostid = self.host_get(hostip)
        if isinstance(grouplist,list):
            grouplist = grouplist 
        else:
            grouplist = grouplist.split()
        if hostid == 0:
            print '\t',"\033[1;31;40m%s\033[0m" % "This host cannot find in zabbix,please check it !"
            sys.exit()
        else:
            for i in grouplist:
                a = self.group_get(i)
                if a != 0:
                    data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "host.massadd",
                        "params": {
                            "hosts":[{"hostid": hostid}],
                            "groups": [
                                {"groupid": a}
                            ]
                        },
                        "auth": self.authID,
                        "id": 1
                        })
                    res = self.get_data(data)['result']
                    if (res != 0) and (len(res) !=0 ):
                        print '\t',"\033[1;31;40m%s\033[0m" % "Add group %s to %s success!" % (i,hostip)
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % "Group %s cannot find in zabbix" % i
                    return 0

    def host_remove_groups(self,hostip,grouplist):
        hostid = self.host_get(hostip)
        if hostid == 0:
            print '\t',"\033[1;31;40m%s\033[0m" % "未发现主机 %s 撤销失败！" % hostip
            sys.exit()
        if isinstance(grouplist,list):
            grouplist = grouplist 
        else:
            grouplist = grouplist.split()

        for i in grouplist:
            a = self.group_get(i)
            if a != 0:
                data = json.dumps({
                    "jsonrpc": "2.0",
                    "method": "host.massremove",
                    "params": {
                        "hostids": [hostid],
                        "groupids": [a]
                    },
                    "auth": self.authID,
                    "id": 1
                    })
                res = self.get_data(data)['result']
                if (res != 0) and (len(res) !=0 ):
                    print '\t',"\033[1;31;40m%s\033[0m" % u"组 %s 已从主机 %s 上撤销！" % (i,hostip)
            else:
                print '\t',"\033[1;31;40m%s\033[0m" % u"未发现组 %s 撤销失败！" % i
                return 0


    def host_add_templates(self,hostip,templatelist):
        hostid = self.host_get(hostip)
        if isinstance(templatelist,list):
            templatelist = templatelist 
        else:
            templatelist = templatelist.split()
        if hostid == 0:
            print '\t',"\033[1;31;40m%s\033[0m" % "This host cannot find in zabbix,please check it !"
            sys.exit()
        else:
            for i in templatelist:
                a = self.template_get(i)
                if a != 0:
                    data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "host.massadd",
                        "params": {
                            "hosts":[{"hostid": hostid}],
                            "templates": [
                                {"templateid": a}
                            ]
                        },
                        "auth": self.authID,
                        "id": 1
                        })
                    res = self.get_data(data)['result']
                    if (res != 0) and (len(res) !=0 ):
                        print '\t',"\033[1;31;40m%s\033[0m" % "update host template!"
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % "Template %s cannot find in zabbix" % templatelist
                    return 0

    def host_clear_templates(self,hostip,templatelist):
        hostid = self.host_get(hostip)
        if isinstance(templatelist,list):
            templatelist = templatelist 
        else:
            templatelist = templatelist.split()
        if hostid == 0:
            print '\t',"\033[1;31;40m%s\033[0m" % "This host cannot find in zabbix,please check it !"
            sys.exit()
        else:
            for i in templatelist:
                a = self.template_get(i)
                if a != 0:
                    data = json.dumps({
                        "jsonrpc": "2.0",
                        "method": "host.massremove",
                        "params": {
                            "hostids": [hostid],
                            "templateids_clear": [a]
                        },
                        "auth": self.authID,
                        "id": 1
                        })
                    res = self.get_data(data)['result']
                    if (res != 0) and (len(res) !=0 ):
                        print '\t',"\033[1;32;40m%s\033[0m" % "Delete template %s from %s" % (templatelist, hostip)
                else:
                    print '\t',"\033[1;31;40m%s\033[0m" % "Template %s cannot find in zabbix" % templatelist
                    return 0


    def host_interface_get(self,hostid):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostinterface.get",
            "params": {
                "output":["type","useip","ip","dns","port"],
                "hostids": hostid
                },
            "auth": self.authID,
            "id": 1
            })
        res = self.get_data(data)['result']
        interface = res[0]
        print interface
        if interface['type'] == '1':
            if interface['useip'] == '1':
                print "\t","\033[1;31;40m%s\033[0m" % "Listen_IP:","\033[1;31;40m%s\033[0m" % interface['ip'].ljust(15),'\t',"\033[1;31;40m%s\033[0m" % u"Listen_port:","\033[1;31;40m%s\033[0m" % interface['port']
            else:
                print "\t","\033[1;31;40m%s\033[0m" % "Listen_IP:","\033[1;31;40m%s\033[0m" % interface['dns'].ljust(15),'\t',"\033[1;31;40m%s\033[0m" % u"Listen_port:","\033[1;31;40m%s\033[0m" % interface['port']
        else:
            print "\t","\033[1;31;40m%s\033[0m" % "主机未采用agent模式收集数据"
            return 0


    def host_prototype(self,hostip):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostprototype.get",
            "params": {
                "output":"extend",
                "host": hostip
                },
            "auth": self.authID,
            "id": 1
            })
        res = self.get_data(data)['result']
        print res
        if (res != 0) and (len(res) !=0 ):
            host = res[0]

    def sizeformat(self,bytesize):
        i=0
        while int(bytesize) >= 1024:
            bytesize = bytesize/1024;
            i += 1
            if i == 4:
                break
        units = ["Bytes","KB","MB","GB","TB"]
        newsize = round(bytesize,2)
        res = str(newsize) + units[i]
        return res


    def item_get(self,hostip,keys):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output":["itemid","name","key_","lastvalue","status"],
                "search": {
                    "key_": keys
                },
                "sortfield": "name"
                "filter": {"host": [hostip]}
                },
            "auth": self.authID,
            "id": 1
            })
        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            item = res
            return item


    def host_info(self,hostip):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output":["hostid","name","status","host"],
                "selectGroups": ["name"],
                "selectInterfaces": ["type","useip","ip","dns","port"],
                "selectParentTemplates":["name"],
                "selectItems":"extend",
                "filter": {"host": [hostip]}
                },
            "auth": self.authID,
            "id": 1
            })

        res = self.get_data(data)['result']
        if (res != 0) and (len(res) !=0 ):
            for i in res[0]['interfaces']:
                if i['useip'] == '1':
                    print "\t","\033[1;32;40m%s\033[0m" % "Listen_IP:","\033[1;32;40m%s\033[0m" % i['ip'].ljust(15),'\t',"\033[1;32;40m%s\033[0m" % u"Listen_port:","\033[1;32;40m%s\033[0m" % i['port']
                else:
                    print "\t","\033[1;32;40m%s\033[0m" % "Listen_IP:","\033[1;32;40m%s\033[0m" % i['dns'].ljust(15),'\t',"\033[1;32;40m%s\033[0m" % u"Listen_port:","\033[1;32;40m%s\033[0m" % i['port']
            host = res[0]
            if host['status'] == '1':
                print "\t","\033[1;31;40m%s\033[0m" % "Host:","\033[1;31;40m%s\033[0m" % host['host'].ljust(15),'\t',"\033[1;31;40m%s\033[0m" % "Host_Name:","\033[1;31;40m%s\033[0m" % host['name'].encode('GBK'),'\t',"\033[1;31;40m%s\033[0m" % u'未在监控状态'
            elif host['status'] == '0':
                print "\t","\033[1;32;40m%s\033[0m" % "Host:","\033[1;32;40m%s\033[0m" % host['host'].ljust(15),'\t',"\033[1;32;40m%s\033[0m" % "Host_Name:","\033[1;32;40m%s\033[0m" % host['name'].encode('GBK'),'\t',"\033[1;32;40m%s\033[0m" % u'在监控状态'
                L = [g['name'] for g in host['groups']]
                print "\t","\033[1;32;40m%s\033[0m" % "所在组: ","\033[1;32;40m%s\033[0m" % json.dumps(L, encoding="UTF-8", ensure_ascii=False)
                T = [t['name'].encode('GBK') for t in host['parentTemplates']]
                print "\t","\033[1;32;40m%s\033[0m" % "已挂模板: ","\033[1;32;40m%s\033[0m" % json.dumps(T,encoding="UTF-8", ensure_ascii=False)
                if "Template OS Linux" in T:
                    a_mem = self.item_get(hostip,"vm.memory.size[available]")
                    t_mem = self.item_get(hostip,"vm.memory.size[total]")
                    if t_mem[0]['status'] == '0':
                        t_now = self.sizeformat(int(t_mem[0]['lastvalue']))
                        a_now = self.sizeformat(int(a_mem[0]['lastvalue']))
                        print "\t","\033[1;32;40m%s\033[0m" % "可用内存: ","\033[1;32;40m%s\033[0m" % a_now, '\t', "\033[1;32;40m%s\033[0m" % "总内存: ","\033[1;32;40m%s\033[0m" % t_now
                    a_cpu_load = self.item_get(hostip,"system.cpu.load[percpu,avg1]")
                    b_cpu_load = self.item_get(hostip,"system.cpu.load[percpu,avg5]")
                    c_cpu_load = self.item_get(hostip,"system.cpu.load[percpu,avg15]")
                    if a_cpu_load[0]['status'] == '0':
                        one_cpu = str(round(float(a_cpu_load[0]['lastvalue']),2)) + "%"
                        five_cpu = str(round(float(b_cpu_load[0]['lastvalue']),2)) + "%"
                        ten_cpu = str(round(float(c_cpu_load[0]['lastvalue']),2)) + "%"
                        print "\t","\033[1;32;40m%s\033[0m" % "CPU一分钟负载: ","\033[1;32;40m%s\033[0m" % one_cpu,'\t', "\033[1;32;40m%s\033[0m" % "CPU五分钟负载: ","\033[1;32;40m%s\033[0m" % five_cpu,'\t', "\033[1;32;40m%s\033[0m" % "CPU十五分钟负载: ","\033[1;32;40m%s\033[0m" % ten_cpu
                if "Template_TCP_Status" in T:
                    t_listen = self.item_get(hostip,"tcp.status[LISTEN]")
                    t_established = self.item_get(hostip,"tcp.status[ESTAB]")
                    t_syn_recv = self.item_get(hostip,"tcp.status[SYN-RECV]")
                    if t_listen[0]['status'] == '0':
                        print "\t","\033[1;32;40m%s\033[0m" % "TCP_Listen: ","\033[1;32;40m%s\033[0m" % t_listen[0]['lastvalue'], '\t', "\033[1;32;40m%s\033[0m" % "TCP_Established: ","\033[1;32;40m%s\033[0m" % t_established[0]['lastvalue'],'\t', "\033[1;32;40m%s\033[0m" % "TCP_SYN_recv: ","\033[1;32;40m%s\033[0m" % t_syn_recv[0]['lastvalue']
        else:
            print '\t',"\033[1;31;40m%s\033[0m" % "Get Host Error or cannot find this host,please check !"
            return 0