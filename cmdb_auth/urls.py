from django.conf.urls import patterns, include, url
from cmdb_auth.views import auth_index, group_add, group_edit, group_status, group_delete, group_add_auth, cmdb_group_user


urlpatterns = [
    url(r'^cmdb_auth_index/$', auth_index, name='auth_index'),
    url(r'^cmdb_group_add/$', group_add, name='auth_group_add'),
    url(r'^cmdb_group_edit/(?P<uuid>[^/]+)/$', group_edit),
    url(r'^cmdb_group_status/(?P<uuid>[^/]+)/$', group_status),
    url(r'^cmdb_group_delete/(?P<uuid>[^/]+)/$', group_delete),
    url(r'^cmdb_group_auth_add/(?P<uuid>[^/]+)/$', group_add_auth),
    url(r'^cmdb_group_user/(?P<uuid>[^/]+)/$', cmdb_group_user),




]