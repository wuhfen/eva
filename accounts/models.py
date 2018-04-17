#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import validators
from django.contrib.auth.models import BaseUserManager
import random, time
import uuid




def common_uuid():
    """
    :return:
    """
    list_key = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%^&*()_'
    symbol = '!@$%^&*()_'
    key_list = []
    for i in range(60):
        key_list.append(random.choice(list_key))
    for i in range(4):
        key_list.append(random.choice(symbol))
    key_name = "%s%s%s" % (''.join(key_list), time.time(), uuid.uuid4())
    uuid_data = str(uuid.uuid3(uuid.NAMESPACE_DNS, key_name.encode('utf-8')))
    return uuid_data

class DepartmentGroup(models.Model):
    department_groups_name = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'组名')
    description = models.TextField(verbose_name=u"介绍", blank=True, null=True, )

    def __unicode__(self):
        return self.department_groups_name

    class Meta:
        verbose_name = u"部门组"
        verbose_name_plural = verbose_name

class department_Mode(models.Model):
    #组的概念
    name = models.CharField(max_length=64, blank=True,verbose_name=u'组名称')
    manager = models.ForeignKey('CustomUser',verbose_name=u"组长",related_name='group_manager')
    members = models.ManyToManyField('CustomUser',verbose_name=u'所属用户',related_name='group_users')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"成员组"
        verbose_name_plural = verbose_name

class department_auth_cmdb(models.Model):
    """
    cmdb组权限
    所有字段全部以0，1来表示
    1表示有此权限，0表示无此权限
    所有数据全部外键关联user表，当用户删除时相应权限也随之删除
    """
    department_name = models.ForeignKey('department_Mode',related_name='group_auth', verbose_name=u'所属组', help_text=u"添加组权限")
    u"""
    资产组管理
    """
    show_a_group = models.BooleanField(default=False, verbose_name=u"查看资产组")
    add_a_group = models.BooleanField(default=False, verbose_name=u"添加资产组")
    edit_a_group = models.BooleanField(default=False, verbose_name=u"更新资产组")
    delete_a_group = models.BooleanField(default=False, verbose_name=u"删除资产组")

    u"""
    资产管理
    """
    select_host = models.BooleanField(default=False, verbose_name=u"查看资产")
    update_host = models.BooleanField(default=False, verbose_name=u"更新资产")
    add_host = models.BooleanField(default=False, verbose_name=u"添加资产")
    delete_host = models.BooleanField(default=False, verbose_name=u"删除资产")
    show_pro = models.BooleanField(default=False, verbose_name=u"查看项目")
    add_pro = models.BooleanField(default=False, verbose_name=u"添加项目")

    u"""
    发布更新审核权限管理
    """
    money_fabu = models.BooleanField(default=False, verbose_name=u"现金网发布")
    money_gengxin = models.BooleanField(default=False, verbose_name=u"现金网更新")
    manniu_fabu = models.BooleanField(default=False, verbose_name=u"蛮牛发布")
    manniu_gengxin = models.BooleanField(default=False, verbose_name=u"蛮牛更新")
    auth_project = models.BooleanField(default=False, verbose_name=u"展示我的任务")
    auditor_manage = models.BooleanField(default=False, verbose_name=u"审核人管理")
    observer = models.BooleanField(default=False, verbose_name=u"任务状态观察者")
    one_key = models.BooleanField(default=False, verbose_name=u"一键通过权限")

    u"""
    用户和组管理
    """
    add_user = models.BooleanField(default=False, verbose_name=u'添加用户')
    edit_user = models.BooleanField(default=False, verbose_name=u'修改用户')
    edit_pass = models.BooleanField(default=False, verbose_name=u"修改密码")
    delete_user = models.BooleanField(default=False, verbose_name=u"删除用户")
    show_department = models.BooleanField(default=False, verbose_name=u"查看组")
    add_department = models.BooleanField(default=False, verbose_name=u"添加组")
    edit_department = models.BooleanField(default=False, verbose_name=u"修改组")
    delete_department = models.BooleanField(default=False, verbose_name=u"删除组")

    u"""
    白名单管理
    """
    show_white = models.BooleanField(default=False, verbose_name=u"白名单查看")
    edit_white = models.BooleanField(default=False, verbose_name=u"白名单增删改")

    u"""
    域名管理
    """
    show_domain = models.BooleanField(default=False, verbose_name=u"域名查看")
    edit_domain = models.BooleanField(default=False, verbose_name=u"域名修改")
    add_domain = models.BooleanField(default=False, verbose_name=u"域名增加")
    delete_domain = models.BooleanField(default=False, verbose_name=u"域名删除")

    u"""
    备用后台管理
    """
    show_nginx = models.BooleanField(default=False, verbose_name=u"备用后台查看")
    edit_nginx = models.BooleanField(default=False, verbose_name=u"备用后台修改")
    add_nginx = models.BooleanField(default=False, verbose_name=u"备用后台增加")
    delete_nginx = models.BooleanField(default=False, verbose_name=u"备用后台删除")

    u"""
    DNS管理
    """
    show_dns = models.BooleanField(default=False, verbose_name=u"查看dns")

    u"""
    wiki管理
    """
    show_wiki = models.BooleanField(default=False, verbose_name=u"查看wiki")
    add_wiki = models.BooleanField(default=False, verbose_name=u"wiki操作")

    u"""
    测试功能
    """
    test_fun = models.BooleanField(default=False, verbose_name=u"显示未上线测试项目")


    def __unicode__(self):
        return unicode(self.department_name)

    class Meta:
        verbose_name = u"组权限"
        verbose_name_plural = verbose_name

class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        cuuid = common_uuid()
        now = timezone.now()
        if not username:
            raise ValueError('The given Username must be set')
        email = self.normalize_email(email)
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          uuid = cuuid,
                          username = username,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          last_login=now,
                          date_joined=now,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    uuid = models.CharField(max_length=64, unique=True)
    
    username = models.CharField(_(u'用户名'), max_length=30, unique=True)
    email = models.EmailField(_(u'邮箱'), max_length=254, unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=30, blank=False)

    mobile = models.CharField(_(u'Telegram_Bot_Chat_ID'), blank=True,max_length=60)
    session_key = models.CharField(max_length=60, blank=True, null=True, verbose_name=u"session_key")
    user_key = models.TextField(blank=True, null=True, verbose_name=u"用户登录key")
    menu_status = models.BooleanField(default=False, verbose_name=u'用户菜单状态')
    user_active = models.BooleanField(verbose_name=u'设置密码状态', default=0)

    # Admin
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


class server_auth(models.Model):
    server_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=u'服务器')
    user_name = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'用户名')
    first_name = models.CharField(max_length=20, blank=True, null=True, verbose_name=u'姓名')
    auth_weights = models.BooleanField(default=0, verbose_name=u'权限')
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.server_ip

    class Meta:
        verbose_name = u"日志记录"
        verbose_name_plural = verbose_name


if __name__ == '__main__':
    print common_uuid()
