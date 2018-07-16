#!/usr/bin/env python
# coding:utf-8

from celery import shared_task,current_task

from gitfabu.audit_api import task_distributing_by_group

@shared_task()
def sql_send_message_task(tid,gid):
    task_distributing_by_group(tid,gid)
    return "All Message have been send"