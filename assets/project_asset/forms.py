#!/usr/bin/env python
#coding:utf8
from assets.models import Line, Project, Service
from django.forms import ModelForm

class LineForm(ModelForm):
    class Meta:
    	model = Line
    	exclude = ()
    	
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ["project_name",
                  "aliases_name",
                  "project_contact",
                  "description",
                  "line",
                  "sort",
                  "project_user_group",
                  ]

class ServiceForm(ModelForm):
    class Meta:
      model = Service
      exclude = ()