# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2018-02-03 07:35
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Allow_list', '0003_auto_20180123_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='white_list',
            name='ctime',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2018, 2, 3, 7, 33, 45, 422552, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='white_list',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='iptables',
            name='i_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='white_conf',
            name='name',
            field=models.CharField(choices=[('KG-JDC', 'KG\u7ecf\u5178\u5f69\u767d\u540d\u5355'), ('MN-Backend', '\u86ee\u725b\u540e\u53f0\u767d\u540d\u5355'), ('MONEY-Backend', '\u73b0\u91d1\u7f51\u540e\u53f0\u767d\u540d\u5355'), ('MONEY-Black', '\u73b0\u91d1\u7f51\u9ed1\u540d\u5355'), ('MN-Black', '\u86ee\u725b\u9ed1\u540d\u5355')], max_length=25, unique=True, verbose_name='\u767d\u540d\u5355\u914d\u7f6e'),
        ),
        migrations.AlterField(
            model_name='white_list',
            name='git_deploy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='white', to='gitfabu.git_deploy'),
        ),
    ]
