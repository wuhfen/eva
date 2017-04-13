#!/usr/bin/python env
# code:utf-8

import time
import json
import os
from api.ssh_api import ssh_cmd


class init_sys(object):
    """docstring for init_sys"""
    def __init__(self, arg):
        super(init_sys, self).__init__()
        self.arg = arg
        print self.arg

    def set_selinux(self):
        print "state set selinux"
        files = ['/etc/sysconfig/selinux','/etc/selinux/config']
        for file in files:
            f = open(file,'rw')
            lines = f.readlines()
            print lines
            f.close()
        print "end set selinux"


    def rysn_pubkey(self,key):
        print key

    def change_sshport(self,port):
        print port

    def install_basepkg(self,lists):
        print "list"

    def disable_ipv6(self):
        print "ipv6"

    def install_monitor(self,obj):
        print obj

    def install_docker(self,obj):
        print obj

    def open_iptables(self):
        print "iptables"