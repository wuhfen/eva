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


from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.group import Group
from ansible.inventory.host import Host

from ansible.plugins.callback.json import  CallbackModule as minicb

class ResultsCollector(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result,  *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result,  *args, **kwargs):
        self.host_failed[result._host.get_name()] = result

class MyInventory(Inventory):
    """
    this is my ansible inventory object.
    """
    def __init__(self, resource,loader, variable_manager):
        """
        resource的数据格式是一个列表字典，比如
            {
                "group1": {
                    "hosts": [{"hostname": "10.10.10.10", "port": "22", "username": "test", "password": "mypass"}, ...],
                    "vars": {"var1": value1, "var2": value2, ...}
                }
            }
        如果你只传入1个列表，这默认该列表内的所有主机属于my_group组,比如
            [{"hostname": "10.10.10.10", "port": "22", "username": "test", "password": "mypass"}, ...]
        """
        self.resource = resource
        self.loader = loader
        self.variable_manager = variable_manager
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager,host_list=[])
        self.gen_inventory()

    def my_add_group(self, hosts, groupname, groupvars=None):
        """
        add hosts to a group
        """
        my_group = Group(name=groupname)

        # if group variables exists, add them to group
        if groupvars:
            for key, value in groupvars.iteritems():
                my_group.set_variable(key, value)

        # add hosts to group
        for host in hosts:
            # set connection variables
            hostname = host.get("hostname")
            hostip = host.get('ip', hostname)
            hostport = host.get("port")
            username = host.get("username")
            password = host.get("password")
            ssh_key = host.get("ssh_key")
            my_host = Host(name=hostname, port=hostport)
            my_host.set_variable('ansible_ssh_host', hostip)
            my_host.set_variable('ansible_ssh_port', hostport)
            my_host.set_variable('ansible_ssh_user', username)
            my_host.set_variable('ansible_ssh_pass', password)
            my_host.set_variable('ansible_ssh_private_key_file', ssh_key)

            # set other variables 
            for key, value in host.iteritems():
                if key not in ["hostname", "port", "username", "password"]:
                    my_host.set_variable(key, value)
            # add to group
            my_group.add_host(my_host)

        self.inventory.add_group(my_group)

    def gen_inventory(self):
        """
        add hosts to inventory.
        """
        if isinstance(self.resource, list):
            self.my_add_group(self.resource, 'default_group')
        elif isinstance(self.resource, dict):
            for groupname, hosts_and_vars in self.resource.iteritems():
                self.my_add_group(hosts_and_vars.get("hosts"), groupname, hosts_and_vars.get("vars"))


class MyRunner(object):
    """
    This is a General object for parallel execute modules.
    """
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource
        self.results_raw = {}
        self.host_list = []
        for i in self.resource:
            self.host_list.append(i['hostname'])


    def run(self, module_name, module_args):
        """
        run module from andible ad-hoc.
        module_name: ansible module_name
        module_args: ansible module args
        """
        self.results_raw = {'success':{}, 'failed':{}, 'unreachable':{}}

        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()

        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 
                  'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 
                  'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
        options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, 
                  forks=30, remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, 
                  scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)
 
        passwords = dict(sshpass=None, becomepass=None)

        # create inventory and pass to var manager
        inventory = MyInventory(self.resource, loader, variable_manager).inventory            #你要生成自己的inventory
        variable_manager.set_inventory(inventory)

        # create play with tasks
        play_source = dict(
                name="Ansible Play",
                hosts=self.host_list,             #主机ip地址,[]
                gather_facts='no',
                tasks=[dict(action=dict(module=module_name, args=module_args))]   #ansible要执行的命令
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        # actually run it
        tqm = None
        # callback = Jsoncallback()        #ansible命令执行结果收集器
        callback = minicb()
        try:
            tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    options=options,
                    passwords=passwords,
                    # stdout_callback='json',
                    # run_tree=False,
            )
            tqm._stdout_callback = callback
            callrun = tqm.run(play)
            # return callrun

            result = callback.results

        finally:
            if tqm is not None:
                tqm.cleanup()
        # return result
        return result[-1]['tasks'][-1]



class MyTask(MyRunner):
    def __init__(self, *args, **kwargs):
        super(MyTask, self).__init__(*args, **kwargs)

    def push_key(self, user, key):
        """
        push the ssh authorized key to target.
        """
        module_args = 'user="%s" key="%s" state=present' % (user, key)
        results = self.run("authorized_key", module_args)

        return results

    def set_selinux(self,state):
        if state == "disabled":
            module_args = 'state="%s"' % state
        else:
            module_args = 'policy=targeted state="%s"' % state
        
        results = self.run("selinux", module_args)

        return results

class MyPlaybook(object):
    def __init__(self, resource, *args, **kwargs):
        self.resource = resource
        self.results_raw = {}
        self.variable_manager = VariableManager()
        self.loader = DataLoader()
        self.extra_vars = self.variable_manager.extra_vars


    def run_playbook(self, playbooks_list,**kwargs):
        self.results_raw = {'success':{}, 'failed':{}, 'unreachable':{}}
        playbooks=playbooks_list
        # initialize needed objects
        # variable_manager = VariableManager()
        # loader = DataLoader()

        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 
                        'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 
                        'become', 'become_method', 'become_user', 'verbosity', 'check'])
        options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=30, 
                        remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, 
                        scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)

        passwords = dict(sshpass=None, becomepass=None)

        # create inventory and pass to var manager
        inventory = MyInventory(self.resource, self.loader, self.variable_manager).inventory            #你要生成自己的inventory
        self.variable_manager.set_inventory(inventory)
        self.variable_manager.extra_vars = kwargs
        # for key in kwargs:
        #     self.extra_vars[key] = kwargs[key]

        pbex = PlaybookExecutor(playbooks=playbooks, inventory=inventory, variable_manager=self.variable_manager, loader=self.loader, options=options, passwords=passwords)
        callback = ResultsCollector()
        # pbex._tqm._stdout_callback = callback
        # return_code = pbex.run()
        result = pbex.run()
        return result

        # for host, result in callback.host_ok.items():
        #     self.results_raw['success'][host] = result._result

        # for host, result in callback.host_failed.items():
        #     self.results_raw['failed'][host] = result._result['msg']

        # for host, result in callback.host_unreachable.items():
        #     self.results_raw['unreachable'][host]= result._result['msg']

        # return self.results_raw

class MyPlayTask(MyPlaybook):
    def __init__(self, *args, **kwargs):
        super(MyPlayTask, self).__init__(*args, **kwargs)

    def install_zabbix_agent(self, version,server,listenport,listenip,serveractive):
        result = self.run_playbook(['/etc/ansible/install_zabbix_agent.yml'], version=version,server=server,listenip=listenip,listenport=listenport,serveractive=serveractive)
        return result



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