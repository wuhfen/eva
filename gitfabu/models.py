#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from django.db import models
from business.models import Business 
from accounts.models import CustomUser as Users
from accounts.models import department_Mode as Groups

CLASSIFY_CHOICE = (
    ('huidu', u'灰度'),
    ('online', u'生产'),
    ('test', u'测试'),
)
alone = [i.nic_name for i in Business.objects.filter(platform="单个项目")]+[u"源站",u"AG",u"后台",u"源站反代",u"AG反代"]
SERVER_TYPE = [(i, i) for i in tuple(alone)]
TOOL_TYPE = [(i, i) for i in (u"现金网",u"蛮牛",u"单个项目",u"JAVA项目",u"VUE蛮牛")]
NAME_CHOICE = [(i, i) for i in (u"发布",u"更新",u"php更新","发布复核")]

# Create your models here.
class git_coderepo(models.Model):
    """代码仓库配置，相同的地址只会创建一次"""
    platform = models.CharField(verbose_name=u'项目类型',null=True,blank=True,max_length=32,choices=TOOL_TYPE)
    classify = models.CharField(verbose_name=u'环境类型',null=True,blank=True,max_length=32,choices=CLASSIFY_CHOICE)
    title = models.CharField(_(u'标题'), max_length=32)
    ispublic = models.BooleanField(_(u'是否公用库'),default=False)
    isexist = models.BooleanField(_(u'是否已存在'),default=False)
    address = models.CharField(_(u'地址'), max_length=128, blank=True)
    user = models.CharField(_(u'用户'), max_length=64, blank=True)
    passwd = models.CharField(_(u'密码'), max_length=64, blank=True)
    reversion = models.CharField(_(u'当前版本'),null=True,blank=True, max_length=64)
    branch = models.CharField(_(u'当前分支'),null=True,blank=True, max_length=64)
    class Meta:
        verbose_name = u'代码库'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.title

class git_deploy_audit(models.Model):
    """审核人设置"""
    platform = models.CharField(verbose_name=u'项目类型',max_length=32,choices=TOOL_TYPE)
    classify = models.CharField(verbose_name=u'项目类型',max_length=32,choices=CLASSIFY_CHOICE)
    isurgent = models.BooleanField(_(u'紧急审核'),default=False)
    name = models.CharField(verbose_name=u'名称',max_length=64,choices=NAME_CHOICE)
    ischeck = models.BooleanField(_(u'是否审核'),default=False)
    start_time = models.CharField(_(u'审核开始时间'),null=True,blank=True,max_length=45)
    end_time = models.CharField(_(u'审核结束时间'),null=True,blank=True,max_length=45)
    user = models.ManyToManyField(Users)
    group = models.ManyToManyField(Groups)
    manager = models.ForeignKey(Users,verbose_name=u'审核管理员',null=True,blank=True,related_name='manage')
    class Meta:
        verbose_name = u'审核项设置'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name

class my_request_task(models.Model):
    name = models.CharField(_(u'名称'),max_length=64)
    types = models.CharField(_(u'任务类型'),max_length=64,blank=True,default='gx') #新增字段，发布fabu，更新gengxin，发布确认fabuconfirm
    table_name = models.CharField(_(u'关联表'),null=True,blank=True,max_length=64)
    uuid = models.CharField(_(u'表中某字段id'),null=True,blank=True,max_length=64)
    memo = models.TextField(_(u'内容'))
    initiator = models.ForeignKey(Users,verbose_name=u'发起人',related_name="whoami")
    status = models.CharField(_(u'状态'),max_length=64)
    isend = models.BooleanField(_(u'是否完成'),default=False)
    loss_efficacy = models.BooleanField(_(u'是否作废'),default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-end_date"]
        verbose_name = u'我发起的任务'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name

class git_task_audit(models.Model):
    """审核任务模型"""
    request_task = models.ForeignKey(my_request_task,null=True,blank=True,related_name='reqt')
    auditor = models.ForeignKey(Users,verbose_name=u'审核人',related_name="auditor")
    audit_group_id = models.CharField(_(u'审核人所属组'),max_length=64,null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    isaudit = models.BooleanField(_(u'是否审核'),default=False)
    ispass = models.BooleanField(_(u'是否通过'),default=False)
    audit_time = models.DateTimeField(auto_now=True)
    postil = models.TextField(_(u'批注'),null=True,blank=True)
    loss_efficacy = models.BooleanField(_(u'是否过期'),default=False)

    class Meta:
        ordering = ['-create_date']
        verbose_name = u'任务审核'
        verbose_name_plural = verbose_name


class git_ops_configuration(models.Model):
    """服务器配置模型"""
    name = models.CharField(_(u'名称'),max_length=45,choices=SERVER_TYPE)
    classify = models.CharField(verbose_name=u'类型',max_length=32,choices=CLASSIFY_CHOICE)
    platform = models.CharField(verbose_name=u'项目类型',null=True,blank=True,max_length=32,choices=TOOL_TYPE)
    remoteip = models.TextField(_(u'服务器ip'),null=True,blank=True,default='172.16.13.7')
    remotedir = models.TextField(_(u'目录'),null=True,blank=True,default='/data/wwwroot/')
    owner = models.TextField(_(u'属主'),null=True,blank=True,default='www')
    exclude = models.TextField(_(u'排除文件'),null=True,blank=True,default='Logs/')
    rsync_command = models.TextField(_(u'推送前命令'),null=True,blank=True)
    last_command = models.TextField(_(u'生效前命令'),null=True,blank=True)
    class Meta:
        verbose_name = u'服务器配置'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name


class git_deploy_logs(models.Model):
    """发布时日志"""
    name = models.CharField(_(u'类型'),max_length=45,choices=NAME_CHOICE)
    log = models.TextField(_(u'日志'),blank=True)
    update = models.CharField(_(u'类型'),max_length=64,null=True,blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    git_deploy = models.ForeignKey('git_deploy',verbose_name=u'发布项目',null=True,blank=True,related_name='deploy_logs')


class git_deploy(models.Model):
    """代码发布新建站数据模型,有发布任务时会创建/tmp/cmdb-task.lock,没有此文件才可以执行，否则一直sleep状态"""
    name = models.CharField(_(u'名称'),max_length=45,blank=True,default="1001")
    platform = models.CharField(verbose_name=u'项目类型',null=True,blank=True,max_length=32,choices=TOOL_TYPE,default="现金网")
    classify =  models.CharField(_(u'发布类型'),max_length=64,choices=CLASSIFY_CHOICE)
    business = models.ForeignKey(Business,verbose_name=u'关联业务',null=True,blank=True)
    conf_domain = models.BooleanField(_(u'是否需要配置域名'),default=False)
    now_reversion = models.TextField(_(u'当前版本'),null=True,blank=True)
    old_reversion = models.TextField(_(u'历史版本'),null=True,blank=True)
    server = models.ForeignKey(git_ops_configuration,verbose_name=u'服务器配置',related_name='server_dev')
    isdev = models.BooleanField(_(u'开发是否完成配置'),default=False)
    isops = models.BooleanField(_(u'运维是否确认发布完成'),default=False)
    isaudit = models.BooleanField(_(u'审核是否通过'),default=False)
    islog = models.BooleanField(_(u'是否发布完成'),default=False)
    islock = models.BooleanField(_(u'是否有锁'),default=False)
    usepub = models.BooleanField(_(u'是否调用公用库'),default=False)

    class Meta:
        ordering = ['name']
        verbose_name = u'git_发布配置'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name


class git_code_update(models.Model):
    """代码更新数据模型，有更新任务时会创建/tmp/cmdb-task.lock,没有此文件才可以执行，否则一直sleep状态"""
    name = models.CharField(_(u'名称'),max_length=64,null=True,blank=True)
    code_conf = models.ForeignKey(git_deploy,verbose_name=u'配置信息',null=True,blank=True,related_name='deploy_update')
    METHOD_CHOICE = (
        ('web', u'web更新'),
        ('php_pc', u'pc端php代码更新'),
        ('php_mobile', u'手机端php代码更新'),
        ('js_pc', u'pc端js代码更新'),
        ('js_mobile', u'手机端js代码更新'),
        ('php', u'PHP-Pub代码更新'),
        ('js', u'JS-Pub代码更新'),
        ('vue_php', u'VUE-PHP更新'),
        ('vue_wap', u'VUE-手机更新'),
        ('vue_pc', u'VUE-电脑更新'),
        ('config', u'PHP-Config更新'),
    )
    method = models.CharField(max_length=20,null=True,blank=True,choices=METHOD_CHOICE)
    version = models.CharField(_(u'变更版本号'),max_length=64,blank=True)
    branch = models.CharField(_(u'变更分支'),max_length=64,blank=True,default='main')
    web_branches = models.CharField(_(u'web分支'),max_length=64,blank=True,default='main')
    php_pc_branches = models.CharField(_(u'php_pc分支'),max_length=64,blank=True,default='main')
    php_mobile_branches = models.CharField(_(u'php_mobile分支'),max_length=64,blank=True,default='main')
    js_pc_branches = models.CharField(_(u'js_pc分支'),max_length=64,blank=True,default='main')
    js_mobile_branches = models.CharField(_(u'js_mobile分支'),max_length=64,blank=True,default='main')
    config_branches = models.CharField(_(u'config分支'),max_length=64,blank=True,default='main')
    web_release = models.CharField(_(u'web版本'),max_length=64,null=True,blank=True)
    php_pc_release = models.CharField(_(u'php电脑端'),max_length=64,null=True,blank=True)
    php_moblie_release = models.CharField(_(u'php手机端'),max_length=64,null=True,blank=True)
    js_pc_release = models.CharField(_(u'js电脑端'),max_length=64,null=True,blank=True)
    js_mobile_release = models.CharField(_(u'js手机端'),max_length=64,null=True,blank=True)
    config_release = models.CharField(_(u'config版本'),max_length=64,null=True,blank=True)
    last_version = models.TextField(_(u'上个版本'),null=True,blank=True)
    memo = models.TextField(_(u'发布原因'),null=True,blank=True)
    details = models.TextField(_(u'更新详情'),null=True,blank=True)
    isaudit = models.BooleanField(_(u'审核是否通过'),default=False)
    isurgent = models.BooleanField(_(u'是否紧急'),default=False)
    islog = models.BooleanField(_(u'是否更新完成'),default=False)
    isuse = models.BooleanField(_(u'是否在使用中'),default=False)
    execution_time = models.DateTimeField(auto_now=True)
    ctime = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ctime']
        verbose_name = u'git_更新配置'
        verbose_name_plural = verbose_name
    def __unicode__(self):
        return self.name