# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2017-12-26 04:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Allow_list', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='iptables',
            name='i_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
