#!/usr/bin/env python
# coding:utf-8
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import json
import urllib2
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from django.core.urlresolvers import reverse
from ansible.plugins.callback import CallbackBase



import os
import time
import json

def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'json'

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.results = []

    def _new_play(self, play):
        return {
            'play': {
                'name': play.name,
            }
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.name,
            },
            'hosts': {}
        }

    def v2_playbook_on_play_start(self, play):
        self.results.append(self._new_play(play))

    # def v2_playbook_on_task_start(self, task, is_conditional):
    #     self.results[-1]['tasks'].append(self._new_task(task))

    # def v2_runner_on_ok(self, result, **kwargs):
    #     host = result._host
    #     self.results[-1]['tasks'][-1]['hosts'][host.name] = result._result_stats


    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s

        output = {
            'plays': self.results,
            'stats': summary
        }

        self._display.display(json.dumps(output, indent=4, sort_keys=True))
        self.results[0] = output

    # v2_runner_on_failed = v2_runner_on_ok
    # v2_runner_on_unreachable = v2_runner_on_ok
    # v2_runner_on_skipped = v2_runner_on_ok

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

    callback = CallbackModule()
    pbex._tqm._stdout_callback = callback
    return_code = pbex.run()
    results = callback.results
    return  results