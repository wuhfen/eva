#!/usr/bin/env python
# coding:utf-8

import datetime
import json
import urllib2
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from django.core.urlresolvers import reverse

## 引入ansibleAPI，编写调用API的函数
def ansiblex(vars1="1",vars2="2",vars3="3",vars4="4",vars5="5",vars6="6"):
    one_var=vars1
    two_var=vars2
    three_var=vars3
    four_var=vars4
    five_var=vars5
    six_var=vars6

    variable_manager = VariableManager()
    loader = DataLoader()
    inventory = Inventory(loader=loader, variable_manager=variable_manager,  host_list='/etc/ansible/hosts')
    Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
    options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=30, remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)
 
    variable_manager.extra_vars = {'two_var': two_var, 'three_var': three_var,'four_var': four_var, 'five_var': five_var, 'six_var': six_var}
    passwords = {}

    pbex = PlaybookExecutor(playbooks=[one_var], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
    results = pbex.run()
    return results

def ansiblex_domain(vars1="1",vars2="2",vars3="3",vars4="4",vars5="5",vars6="6",vars7="7",vars8="8"):
    one_var=vars1
    two_var=vars2
    three_var=vars3
    four_var=vars4
    five_var=vars5
    six_var=vars6
    seven_var = vars7
    eight_var = vars8

    variable_manager = VariableManager()
    loader = DataLoader()
    inventory = Inventory(loader=loader, variable_manager=variable_manager,  host_list=one_var)
    Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
    options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=30, remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)
 
    variable_manager.extra_vars = {'three_var': three_var,'four_var': four_var, 'five_var': five_var, 'six_var': six_var,'seven_var': seven_var,'eight_var': eight_var}
    passwords = {}

    pbex = PlaybookExecutor(playbooks=[two_var], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
    results = pbex.run()
    return results

def ansiblex_deploy(vars1="1",vars2="2",vars3="3",vars4="4",vars5="5",vars6="6",vars7="7",vars8="8",vars9="9",vars10="10",vars11="11",vars12="12",vars13="13",vars14="14",vars15="15",vars16="16"):
    one_var=vars1
    two_var=vars2
    three_var=vars3
    four_var=vars4
    five_var=vars5
    six_var=vars6
    seven_var = vars7
    eight_var = vars8
    nine_var = vars9
    ten_var = vars10
    eleven_var = vars11
    twelve_var = vars12
    thirteen_var = vars13
    fourteen_var = vars14
    fifteen_var = vars15
    sixteen_var = vars16

    variable_manager = VariableManager()
    loader = DataLoader()
    inventory = Inventory(loader=loader, variable_manager=variable_manager,  host_list=one_var)
    Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
    options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=30, remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)
 
    variable_manager.extra_vars = {'three_var': three_var,'four_var': four_var, 'five_var': five_var, 'six_var': six_var,'seven_var': seven_var,'eight_var': eight_var,'nine_var': nine_var,'ten_var': ten_var, 'eleven_var':eleven_var, 'twelve_var':twelve_var,'thirteen_var':thirteen_var,'fourteen_var':fourteen_var,'fifteen_var':fifteen_var, 'sixteen_var':sixteen_var}
    passwords = {}

    pbex = PlaybookExecutor(playbooks=[two_var], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
    results = pbex.run()
    return results