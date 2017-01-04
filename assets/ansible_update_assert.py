#!/usr/bin/env python
# coding:utf-8
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from assets.models import IDC, Service, Line, Project, sqlpasswd
from assets.models import Asset, Server, NIC, RaidAdaptor, Disk, CPU, RAM
from forms import ServerForm, AssetForm, CPUForm, RAMForm, DiskForm, NICForm, RaidForm, SQLpassForm
# Create your views here.

from api.common_api import create_ansible_inventory,gen_resource
from api.ansible_api import MyRunner
import re
import traceback

#     L = [ip,port,user,password,uuid]
# asset_ansible_update(L)
# create_ansible_inventory(hostip_list,groupname)

def ansible_record(asset, ansible_dic):
    alert_dic = {}
    asset_dic = asset.__dict__
    for field, value in ansible_dic.items():
        old = asset_dic.get(field)
        new = ansible_dic.get(field)
        if unicode(old) != unicode(new):
            setattr(asset, field, value)
            asset.save()

def ansible_record_cpu(cpu,ansible_dic):
    cpu_dic = cpu.__dict__
    for field, value in ansible_dic.items():
        old = cpu_dic.get(field)
        new = ansible_dic.get(field)
        if unicode(old) != unicode(new):
            setattr(cpu, field, value)
            cpu.save()

def ansible_record_nic(nic,ansible_dic):
    nic_dic = nic.__dict__
    for field, value in ansible_dic.items():
        old = nic_dic.get(field)
        new = ansible_dic.get(field)
        if unicode(old) != unicode(new):
            setattr(nic, field, value)
            nic.save()

def get_ansible_asset_info(asset_ip, setup_info):
    disk_need = {}
    disk_all = setup_info.get("ansible_devices")
    if disk_all:
        for disk_name, disk_info in disk_all.iteritems():
            if disk_name.startswith('sd') or disk_name.startswith('hd') or disk_name.startswith('vd') or disk_name.startswith('xvd'):
                disk_size = disk_info.get("size", '')
                if 'M' in disk_size:
                    disk_format = round(float(disk_size[:-2]) / 1000, 0)
                elif 'T' in disk_size:
                    disk_format = round(float(disk_size[:-2]) * 1000, 0)
                else:
                    disk_format = float(disk_size[:-2])
                disk_need[disk_name] = disk_format
    all_ip = setup_info.get("ansible_all_ipv4_addresses")
    other_ip_list = all_ip.remove(asset_ip) if asset_ip in all_ip else []
    other_ip = ','.join(other_ip_list) if other_ip_list else ''

    hostname = setup_info.get("ansible_hostname")

    nic_need = {}
    all_interfaces = setup_info.get("ansible_interfaces")
    other_face_list = [i for i in all_interfaces if i != 'lo']

    print other_face_list
    for i in other_face_list:
        interface = "ansible_" + i
        print interface
        print setup_info.get(interface)
        if setup_info.get(interface).has_key("ipv4"):
            interface_ip = setup_info.get(interface).get("ipv4").get("address")
            interface_netmask = setup_info.get(interface).get("ipv4").get("netmask")
            interface_mac = setup_info.get(interface).get("macaddress")
            ip_info = [i,interface_mac,interface_ip,interface_netmask]
            nic_need[i] = ip_info

    nic = nic_need
    # ip = setup_info.get("ansible_default_ipv4").get("address")

    mac = setup_info.get("ansible_default_ipv4").get("macaddress")
    brand = setup_info.get("ansible_product_name")
    try:
        cpu_type = setup_info.get("ansible_processor")[1]
    except IndexError:
        cpu_type = ' '.join(setup_info.get("ansible_processor")[0].split(' ')[:6])

    memory = setup_info.get("ansible_memtotal_mb")
    try:
        memory_format = int(round((int(memory) / 1000), 0))
        memory_format= 1 if memory_format == 0 else 2
    except Exception:
        memory_format = memory

    disk = 0
    for k,v in disk_need.iteritems():
        disk = disk + v

    system_type = setup_info.get("ansible_distribution")
    if system_type.lower() == "freebsd":
        system_version = setup_info.get("ansible_distribution_release")
        cpu_counts = setup_info.get("ansible_processor_count")
    else:
        system_version = setup_info.get("ansible_distribution_version")
        cpu_counts = setup_info.get("ansible_processor_vcpus")
    system_kernel = setup_info.get("ansible_kernel")
    cpu = cpu_type + ' * ' + unicode(cpu_counts)
    cpu_cores = setup_info.get("ansible_processor_cores")
    system_arch = setup_info.get("ansible_architecture")
    asset_type = setup_info.get("ansible_system")
    sn = setup_info.get("ansible_product_serial")
    asset_info = [hostname,memory_format,disk,cpu_type,cpu_counts,cpu_cores,asset_type,system_type,system_version,system_kernel,nic]
    # asset_info = [other_ip, mac, cpu, memory_format, disk, sn, system_type, system_version, brand, system_arch,other_face_list]
    return asset_info

def asset_ansible_update(obj_list,asset_type):
    resource = gen_resource(obj_list)
    ansible_instance = MyRunner(resource)

    ansible_asset_info = ansible_instance.run(module_name='setup', module_args='filter=*')
    for asset in obj_list:
        try:
            setup_info = ansible_asset_info["hosts"][asset.ssh_host]['ansible_facts']
        except KeyError, e:
            continue
        else:
            try:
                asset_info = get_ansible_asset_info(asset.ssh_host, setup_info)
                print asset_info
                hostname,memory,disk,cpu_type,cpu_counts,cpu_cores,asset_type,system_type,system_version,system_kernel,nic = asset_info
                cpu_dic = {
                            "cpu_model": cpu_type,
                            "cpu_count": cpu_counts,
                            "cpu_core_count": cpu_cores
                            }
                nic_list = []
                for k,v in nic.iteritems():
                    k = {}
                    k["name"] = v[0]
                    k["macaddress"] = v[1]
                    k["ipaddress"] = v[2]
                    k["netmask"] = v[-1]
                    nic_list.append(k)

                asset_dic = {
                             "name": hostname,
                             "RAM_total": memory,
                             "Disk_total": disk,
                             "os_type": asset_type,
                             "os_version": system_type,
                             "os_release": system_version,
                             "os_kernel": system_kernel,
                             }
                # print asset_dic
                print nic_list
                # print cpu_dic
                cpu_data = asset.asset.cpu
                nic_obj_all = asset.asset.nic_set.all()
                if not nic_obj_all:
                    for i in nic_list:
                        aa = NIC(asset=asset.asset,name=i['name'],macaddress=i['macaddress'],ipaddress=i['ipaddress'],netmask=i['netmask'],memo=u"内网")
                        aa.save()
                else:
                    for i in nic_obj_all:
                        for j in nic_list:
                            if j['name'] == i.name:
                                ansible_record_nic(i,j)

                ansible_record_cpu(cpu_data,cpu_dic)
                ansible_record(asset, asset_dic)
            except Exception as e:

                traceback.print_exc()
