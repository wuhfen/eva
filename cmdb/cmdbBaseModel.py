#!/usr/bin/env python
# coding:utf-8

from django.db import models
import json

class BaseModel(models.Model):
    class Meta:
        abstract = True

    def getMtMField(self):
        """返回self._meta.fields中没有的，但是又是需要的字段名的列表,形如['name','type']"""
        pass

    def getIgnoreList(self):
        """返回需要在json中忽略的字段名的列表,形如['password']
        """
        pass

    def isAttrInstance(self, attr, clazz):
        return isinstance(getattr(self, attr), clazz)

    def getDict(self):
        fields = []
        for field in self._meta.fields:
            fields.append(field.name)

        d = {}
        import datetime
        for attr in fields:
            if isinstance(getattr(self, attr), datetime.datetime):
                d[attr] = getattr(self, attr).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(getattr(self, attr), datetime.date):
                d[attr] = getattr(self, attr).strftime('%Y-%m-%d')
            # 特殊处理datetime的数据
            elif isinstance(getattr(self, attr), BaseModel):
                d[attr] = getattr(self, attr).getDict()
            # 递归生成BaseModel类的dict
            elif self.isAttrInstance(attr, int) or self.isAttrInstance(attr, float) \
                    or self.isAttrInstance(attr, str):
                d[attr] = getattr(self, attr)
            else:
                d[attr] = getattr(self, attr)

        mAttr = self.getMtMField()
        if mAttr is not None:
            for m in mAttr:
                if hasattr(self, m):
                    attlist = getattr(self, m).all()
                    l = []
                    for attr in attlist:
                        if isinstance(attr, BaseModel):
                            l.append(attr.getDict())
                        else:
                            dic = attr.__dict__
                            if '_state' in dic:
                                dic.pop('_state')
                            l.append(dic)
                    d[m] = l
        # 由于ManyToMany类不能存在于_meat.fields，因而子类需要在getMtMFiled中返回这些字段
        if 'basemodel_ptr' in d:
            d.pop('basemodel_ptr')

        ignoreList = self.getIgnoreList()
        if ignoreList is not None:
            for m in ignoreList:
                if d.get(m) is not None:
                    d.pop(m)
        # 移除不需要的字段
        return d

    def toJSON(self):
        import json
        _data = self.getDict()
        return json.dumps(_data, ensure_ascii=False).encode('utf-8').decode()