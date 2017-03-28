#!/usr/bin/python env
# -- coding:utf-8 --

import json
import urllib2,urllib
import socket

class DNSPod(object):
    """docstring for DNSPod"""
    def __init__(self, user,passwd,paltform,user_token=None):
        super(DNSPod, self).__init__()
        self.user = user
        self.passwd = passwd
        self.paltform = paltform
        if self.paltform == "PODCN":  #如果是dns国内版，直接给user_token
            self.url = 'https://dnsapi.cn/'
            self.record_line = "默认"
            self.headers = { 'User-Agent' : 'DS DDNS Client/1.0.0 ('+user+')' }
            self.token_method = "login_token"
            if user_token:
                self.user_token = user_token
                print self.user_token
            else:
                print "No Token Error!"
                return None
        elif self.paltform == "PODCOM": #如果是国际版，调用get_token函数，获取user_token
            self.url = 'https://api.dnspod.com/'
            self.record_line = "default"
            self.headers = { 'User-Agent' : 'MJJ DDNS Client/1.0.0 ('+user+')' }
            self.token_method = "user_token"
            self.user_token = self.pod_get_token()
            # print "init-get-token %s"% self.user_token

    def post_http(self,url,values):
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data, self.headers)
        try:
            response = urllib2.urlopen(req,timeout = 20)
            the_page = response.read()
        except urllib2.URLError:
            the_page = {'status': {'message': 'connection timeout', 'code': '105'}}
            return the_page
        except socket.timeout:
            the_page = {'status': {'message': 'connection timeout', 'code': '108'}}
            return the_page

        return json.loads(the_page.decode('utf-8'))
        # return json.loads(the_page)



    def pod_get_token(self):
        url = self.url + "Auth"
        values = {
            'login_email': self.user,
            'login_password': self.passwd,
            'format' : 'json'
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            print res["user_token"]
            return res["user_token"]
        print res["status"]["message"]
        return res["status"]

    def pod_domain_add(self,domain):
        """添加一条域名，需要在域名购买的网站，将域名绑定到dnspod的DNS服务器"""
        url = self.url + "Domain.Create"

        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain' : domain
            }
        res = self.post_http(url,values)
        # if res["status"]["code"] == "1":
        #     return res["domain"]["id"]
        # else:
        #     print res["status"]["message"]
        return res

    def pod_domain_list(self):
        url = self.url + "Domain.List"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            return res["domains"]
            print res["info"]
        else:
            print res["status"]["message"]
            return res["status"]

    def pod_domain_delete(self,domain):
        url = self.url + "Domain.Remove"
        if '.' in domain:
            keys = "domain"
        else:
            keys = "domain_id"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            keys : domain
        }
        res = self.post_http(url,values)
        print type(res)
        print res
        print res["status"]
        if res["status"]["code"] == "1":
            return res["status"]["code"]
        else:
            print res["status"]["message"]
            return res["status"]

    def pod_domain_status(self,status,domain):
        """域名禁用启用"""
        url = self.url + "Domain.Status"
        if '.' in domain:
            keys = "domain"
        else:
            keys = "domain_id"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'status' : status,
            keys : domain,
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            return res["status"]["code"]
        else:
            print res["status"]["message"]
            return res["status"]

    def pod_domain_info(self,domain):
        url = self.url + "Domain.Info"
        if '.' in domain:
            keys = "domain"
        else:
            keys = "domain_id"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            keys : domain,
        }
        res = self.post_http(url,values)
        # if res["status"]["code"] == "1":
        #     return res["domain"]
        # print res["status"]["message"]
        # return res["status"]
        return res

    def pod_record_add(self,domain,sub_domain,record_type,value,mx=None,ttl=None):
        """添加记录函数: qq.com, 360, A, 119.97.45.1, default, 600  记录为360.qq.com ---> 119.97.45.1"""
        url = self.url + "Record.Create"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain,
            'sub_domain' : sub_domain,
            'record_type' : record_type,
            'record_line' : self.record_line,
            'value' : value,
        }
        if mx:
            values['mx'] = mx
        if ttl:
            values['ttl'] = ttl
        res = self.post_http(url,values)
        return res
        # if res["status"]["code"] == "1":
        #     if res.has_key('record'):
        #         return res["record"]["id"]
        # print res["status"]["message"]
        # return res["status"]

#{u'status': {u'message': u'Action completed successful', u'code': u'1', u'created_at': u'2017-03-25 13:45:37'},
#u'record': {u'status': u'enabled', u'id': u'288383928', u'weight': None, u'name': u'www'}}



    def pod_record_list(self,domain_id):
        """查询record记录，返回record列表"""
        url = self.url + "Record.List"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain_id,
        }
        res = self.post_http(url,values)
        # if res["status"]["code"] == "1":
        #     if res.has_key('records'):
        #         return res["records"]
        # print res["status"]["message"]
        return res

    def pod_record_modify(self,domain,record_id,sub_domain,record_type,value,mx=None,ttl=None):
        """修改记录，如360.qq.com -- 119.97.45.1修改为360.qq.com ---- 119.23.4.1"""
        url = self.url + "Record.Modify"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain,
            'record_id': record_id,
            'sub_domain' : sub_domain,
            'record_type' : record_type,
            'record_line' : self.record_line,
            'value' : value,
        }
        if mx:
            values['mx'] = mx
        if ttl:
            values['ttl'] = ttl
        res = self.post_http(url,values)
        # if res["status"]["code"] == "1":
        #     return res["status"]["code"]
        #     #print res  重复修改返回code1，但是没有record
        #     # if res.has_key('record'):
        #     #     return res["record"]["id"]
        # print res["status"]["message"]
        return res

    def pod_record_remove(self,domain,record_id):
        """删除记录"""
        url = self.url + "Record.Remove"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain,
            'record_id': record_id,
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            return res["status"]["code"]
        print res["status"]["message"]
        return res["status"]

    def pod_record_info(self,domain,record_id):
        url = self.url + "Record.Info"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain,
            'record_id': record_id,
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            if res.has_key('record'):
                return res["record"]
        print res["status"]["message"]
        return res["status"]

    def pod_record_status(self,domain,record_id,status):
        url = self.url + "Record.Status"
        if status:
            new_status = 'enable'
        else:
            new_status = 'disable'

        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain,
            'record_id': record_id,
            'status': new_status
        }
        res = self.post_http(url,values)
        return res
        # if res["status"]["code"] == "1":
        #     if res.has_key('record'):
        #         return res["record"]["id"]
        # print res["status"]["message"]
        # return res["status"]

    def podcn_batch_domain_create(self,domains,record_value=None):
        """批量操作国际版pod竟然没有"""
        url = "https://dnsapi.cn/Batch.Domain.Create"
        if record_value == None:
            record_value = ''
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domains' : domains,  #多个域名之间以英文的逗号分割
            'record_value' : record_value,  #为每个域名添加 @ 和 www 的 A 记录值，记录值为IP，可选，如果不传此参数或者传空，将只添加域名，不添加记录
        }
        res = self.post_http(url,values)
        # if res["status"]["code"] == "1":
        #     return res["job_id"]
        # print res["status"]["message"]
        # return res["status"]
        return res

    def podcn_batch_record_create(self,domain_ids,records):
        """domain_id 域名ID，多个 domain_id 用英文逗号进行分割
        records 待批量添加的记录详情，JSON 字符串。形如：
        [{“sub_domain”:”www,wap,bbs”,”record_type”:”A”,”record_line”:”默认”,”value”:”11.22.33.44”,”ttl”:600},{“sub_domain”:””,”record_type”:”MX”,”record_line”:”默认”,”value”:”mx.qq.com”,”ttl”:600,”MX”:10}]
        """
        url = "https://dnsapi.cn/Batch.Record.Create"
        record_list = []
        for i in records:
            Aa = {"record_line": self.record_line,"ttl":600}
            Aa["sub_domain"] = i["sub_domain"]
            Aa["record_type"] = i["record_type"]
            Aa["value"] = i["value"]
            record_list.append(Aa)
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'domain_id' : domain_ids,
            'records' : json.dumps(record_list),
        }
        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            return res["job_id"]
        print res["status"]["message"]
        return res["status"]

    def podcn_batch_record_modify(self,record_id,change,change_to,value=None,mx=None):
        """record_id 记录的ID，多个 record_id 用英文的逗号分割
        change 要修改的字段，可选值为 [“sub_domain”、”record_type”、”area”、”value”、”mx”、”ttl”、”status”] 中的某一个
        change_to 修改为，具体依赖 change 字段，必填参数
        value 要修改到的记录值，可选，仅当 change 字段为 “record_type” 时为必填参数
        mx MX记录优先级，可选，仅当修改为 MX 记录时为必填参数
        """
        url = "https://dnsapi.cn/Batch.Record.Modify"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'record_id' : record_id,
            'change' : change,
            'change_to' : change_to,
        }
        if change == "mx":
            values['mx'] = mx
        if change == "record_type":
            values['value'] = value

        res = self.post_http(url,values)
        if res["status"]["code"] == "1":
            return res["job_id"]
        print res["status"]["message"]
        return res["status"]

    def podcn_batch_job_status(self,job_id):
        url = "https://dnsapi.cn/Batch.Detail"
        values = {
            self.token_method : self.user_token,
            'format' : 'json',
            'job_id' : job_id,
        }
        res = self.post_http(url,values)
        return res
        # if res["status"]["code"] == "1":
        #     status = {'total':res["total"],'success':res["success"],'fail':res["fail"]}
        #     return status
        # print res["status"]["message"]
        # return res["status"]["message"]