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


auth_gid = [(1001, u"运维部"), (1002, u"架构"), (1003, u"研发dev"), (1004, u"测试")]

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
    department_name = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'部门名称')
    description = models.TextField(verbose_name=u"介绍", blank=True, null=True, )
    desc_gid = models.IntegerField(verbose_name=u"部门组", choices=auth_gid, blank=True, null=True, )

    def __unicode__(self):
        return self.department_name

    class Meta:
        verbose_name = u"部门"
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
    username = models.CharField(_(u'用户名'), max_length=30, unique=True)
    email = models.EmailField(_(u'邮箱'), max_length=254, unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=30, blank=False)

    department = models.ForeignKey(department_Mode, blank=True, null=True, verbose_name=u"部门", related_name="users")
    mobile = models.CharField(_(u'手机'), max_length=30, blank=False,
                              validators=[validators.RegexValidator(r'^[0-9+()-]+$',
                                                                    _('Enter a valid mobile number.'),
                                                                    'invalid')])
    session_key = models.CharField(max_length=60, blank=True, null=True, verbose_name=u"session_key")
    user_key = models.TextField(blank=True, null=True, verbose_name=u"用户登录key")
    menu_status = models.BooleanField(default=False, verbose_name=u'用户菜单状态')
    user_active = models.BooleanField(verbose_name=u'设置密码状态', default=0)
    uuid = models.CharField(max_length=64, unique=True)

    # uuid = models.CharField(default=str(uuid.uuid3(uuid.NAMESPACE_DNS, hashlib.md5(str(time.time()) + str("".join(
    #         [random.choice("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@$%^&*()_") for i in
    #          range(60)])) + str(uuid.uuid4())).hexdigest())), max_length=64)

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
