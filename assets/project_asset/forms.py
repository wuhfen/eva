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
        fields = ["project_name","parent","sort"]

class ServiceForm(ModelForm):
    class Meta:
      model = Service
      exclude = ()