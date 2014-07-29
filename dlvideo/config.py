#!/usr/bin/env python
# coding=utf-8

import os
from vavava.util import script_path as _script_path

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class Config:
    def __init__(self, config='config.ini'):
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        if os.path.exists(config):
            cfg.read(pabspath(config))
        else:
            cfg.read(pjoin(_script_path(__file__), config))
        self.out_dir = cfg.get('default', 'out_dir')
        self.format = cfg.getint('default', 'format')
        self.dl_method = cfg.get('default', 'dl_method')
        self.nthread = cfg.getint('network', 'nthread')
        self.nperfile = cfg.getint('network', 'nperfile')
        self.log = cfg.get('default', 'log')
        self.log_level = cfg.get('default', 'log_level')
        self.lib_dir = cfg.get('script', 'lib_dir')
        self.cmd = cfg.get('script', 'cmd')
        self.u2b_cmd = cfg.get('u2b', 'cmd')
        self.u2b_proxy = cfg.get('u2b', 'proxy')
        self.u2b_cache = cfg.get('u2b', 'cache')
        self.u2b_title_format = cfg.get('u2b', 'title_format', raw=True)
        self.u2b_create_dir = cfg.get('u2b', 'create_dir')
        self.flvcd = {}
        for k,v in cfg.items('flvcd'):
            self.flvcd[k] = v.lower() == 'true'
        lvlconvert = {
            'critical' : 50,
            'fatal' : 50,
            'error' : 40,
            'warning' : 30,
            'warn' : 30,
            'info' : 20,
            'debug' : 10,
            'notset' : 0
        }
        if self.log_level:
            self.log_level = lvlconvert[self.log_level.strip().lower()]
