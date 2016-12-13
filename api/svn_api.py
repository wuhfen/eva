#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement
from subprocess import Popen, STDOUT, PIPE
try:
    from urllib import unquote
except: #python 3
    from urllib.parse import unquote
import re
import os.path
import json


class SVNException(Exception):
    """Exception class allowing a exit_code parameter and member
    to be used when calling Git to return exit code"""
    def __init__(self, msg, exit_code=None):
        super(SVNException, self).__init__(msg)
        self.exit_code = exit_code


class Revision(object):
    """A representation of a revision.
    Available fields are::
      node, rev, author, branch, parents, date, tags, desc
    A Revision object is equal to any other object with the same value for node
    """
    def __init__(self, json_log):
        """Create a Revision object from a JSON representation"""
        rev = json.loads(json_log)

        for key in rev.keys():
            self.__setattr__(key, unquote(rev[key]))

        if not self.parents:
            self.parents = []
        else:
            self.parents = self.parents.split()

    def __eq__(self, other):
        """Returns true if self.node == other.node"""
        return self.node == other.node




class Svnrepo(object):
    def __init__(self, path,user,password):
        self.path = path
        self.cfg = False
        self.user = user
        self.password = password

    def __getitem__(self, rev):
        """Get a Revision object for the revision identifed by rev"""
        return self.revision(rev)


    @classmethod
    def command(cls, path,user,password, *args):
        """Run a git command in path and return the result. Throws on error."""
        if not path:
            path = '.'
        anv = ["svn"] + ["--username",user,"--password",password] + list(args)
        #return anv
        proc = Popen(" ".join(anv),shell=True,stdout=PIPE, stderr=PIPE, cwd=path)
    
        out, err = [x.decode("utf-8") for x in  proc.communicate()]

        if proc.returncode:
            cmd = "svn " + " ".join(args)
            raise SVNException("Error running %s:\n\tErr: %s\n\tOut: %s\n\tExit: %s"
                            % (cmd,err,out,proc.returncode), exit_code=proc.returncode)
        #out = proc.communicate()
        return out

    def svn_command(self, *args):

        return Svnrepo.command(self.path,self.user,self.password, *args)

    def svn_update(self,reversion=None,*args):
        if reversion == "all":
            self.svn_command("update",*args)
        else:
            self.svn_command("update","-r",str(reversion),*args)



    def svn_checkout(self,url,ccdir=None,*args):
        if ccdir:
            self.svn_command("checkout",url,ccdir,*args)
        else:
            self.svn_command("checkout",url,*args)

    def svn_get_reversion(self,logfile=None,limit=None):
        cmds = []
        if limit: 
            cmds.extend(['--limit',str(limit)])
        else:
            cmds.extend(["--limit","20"])
        if logfile: 
            cmds.extend([">",logfile])
        else:
            cmds.extend([">","/tmp/svn_reversion_log"])

        res = self.svn_command("log","-q",*cmds)
    #return res
        xargs = []
        if logfile:
            f = open(logfile,'r+')
        else:
            f = open('/tmp/svn_reversion_log','r+')
        for x in f.readlines():
            if re.match(r'(\w+)(\d+)',x):
                m = re.match(r'^r(\d+) \| (\w+).*',x)
                xargs += [m.group(1) + "_" +  m.group(2)]
        return xargs