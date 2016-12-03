from django.conf.urls import patterns, include, url
from django.contrib.auth.views import password_change

import accounts.views
import accounts.tests
import accounts.account
import accounts.user_mode.user_edit_class


urlpatterns = [
	url(r'^login/$', accounts.account.user_login,name='user_login'),
    url(r'^logout/$', accounts.account.user_logout),

	url(r'^newpasswd/$', accounts.account.new_password),
	url(r'^changepasswd/$', password_change,{'template_name': 'accounts/change_password.html', 'post_change_redirect': '/accounts/login/'}),
	url(r'^forgetpasswd/$', accounts.account.forgetpasswd,name='forgetpasswd'),
	url(r'user_list/$', accounts.views.user_select, name='user_list'),
	url(r'register/$', accounts.views.register, name='add_user'),
    url(r'^old/$', accounts.views.user_old, name='old_user'),
    url(r'^user_forbidden/$', accounts.views.user_forbidden, name='forbidden_user'),

    url(r'user_edit/(?P<id>\d+)/$', accounts.user_mode.user_edit_class.user_edit),
    url(r'^status/(?P<id>\d+)/$', accounts.views.user_status),
    url(r'^delete/(?P<id>\d+)/$', accounts.views.user_delete),

    url(r'^list_department/$', accounts.views.department_list, name='department_list'),
    url(r'add_department/$', accounts.views.department_view, name='department_add'),
    url(r'department/edit/(?P<id>\d+)/$', accounts.views.department_edit),
    url(r'test/$', accounts.tests.username_login),


    # url(r'^$', index),
]