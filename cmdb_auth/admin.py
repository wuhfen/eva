from django.contrib import admin
from models import *

# Register your models here.
admin.site.register(auth_group)
admin.site.register(user_auth_cmdb)

admin.site.register(AuthSudo)

# admin.site.register(auth_group)
