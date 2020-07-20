# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2018-07-16 17:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20180417_1932'),
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='sql_apply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('database', models.CharField(blank=True, max_length=28)),
                ('sql_type', models.CharField(blank=True, choices=[('\u6587\u4ef6', '\u6587\u4ef6'), ('\u8bed\u53e5', '\u8bed\u53e5')], max_length=10)),
                ('md5v', models.CharField(blank=True, max_length=45)),
                ('statement', models.TextField(blank=True)),
                ('file_path', models.TextField(blank=True)),
                ('file_name', models.TextField(blank=True)),
                ('status', models.CharField(blank=True, max_length=20)),
                ('isaudit', models.BooleanField(default=False)),
                ('islog', models.BooleanField(default=False)),
                ('log', models.TextField(blank=True, null=True)),
                ('memo', models.TextField(blank=True, null=True)),
                ('etime', models.DateTimeField(auto_now=True)),
                ('ctime', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '\u6570\u636e\u5e93\u6267\u884c\u7533\u8bf7',
                'verbose_name_plural': '\u6570\u636e\u5e93\u6267\u884c\u7533\u8bf7',
            },
        ),
        migrations.CreateModel(
            name='sql_conf',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=128, verbose_name='\u540d\u79f0')),
                ('pub_vip', models.CharField(blank=True, max_length=15, verbose_name='\u516c\u7f51VIP')),
                ('local_vip', models.CharField(blank=True, max_length=15, verbose_name='\u5185\u7f51VIP')),
                ('vip_port', models.CharField(default=3306, max_length=6, verbose_name='VIP\u8c03\u7528\u7aef\u53e3')),
                ('cluster', models.BooleanField(default=False, verbose_name='\u662f\u5426\u4e3a\u96c6\u7fa4')),
                ('main_node', models.GenericIPAddressField(verbose_name='\u4e3b\u8282\u70b9')),
                ('subordinate_node', models.TextField(blank=True, null=True, verbose_name='\u4ece\u8282\u70b9')),
                ('user', models.CharField(default='root', max_length=28)),
                ('port', models.CharField(default=3306, max_length=6)),
                ('password', models.CharField(max_length=100)),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.department_Mode')),
            ],
        ),
#        migrations.RemoveField(
#            model_name='task_audit',
#            name='auditor',
#        ),
#        migrations.RemoveField(
#            model_name='task_audit',
#            name='gengxin',
#        ),
#        migrations.RemoveField(
#            model_name='task_audit',
#            name='initiator',
#        ),
#        migrations.DeleteModel(
#            name='task_audit',
#        ),
        migrations.AddField(
            model_name='sql_apply',
            name='name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='audit.sql_conf'),
        ),
    ]
