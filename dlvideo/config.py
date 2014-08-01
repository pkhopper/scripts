#!/usr/bin/env python
# coding=utf-8

import os
from vavava import util

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class Config:
    def __init__(self, config='dlvideo.ini', script=__file__):
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        if os.path.exists(config):
            cfg.read(pabspath(config))
        else:
            cfg.read(pjoin(util.script_path(script), config))
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


def parse_args(config, argv):
    import argparse
    usage = """./dlvideo [-m][-l][-c config][-o output][-f format] url ..."""
    parser=argparse.ArgumentParser(prog=argv, usage=usage, description='download net video', version='0.1')
    parser.add_argument('urls', nargs='*', help='urls')
    # parser.add_argument('urls', nargs='+', help='urls')
    parser.add_argument('-c', '--config', default='dlvideo.ini')
    parser.add_argument('-o', '--out_dir', default=config.out_dir)
    parser.add_argument('-i', '--interact', action='store_true')
    parser.add_argument('-l', '--play-list', dest='play_list', action='store_true')
    parser.add_argument('-f', '--format', help='0,1,2,3',choices=['0', '1', '2', '3'])
    parser.add_argument('--dl_method', default=config.dl_method)
    args = parser.parse_args()
    # print args
    return args

def init_args_config(argv, script):
    config = Config(script=script)
    args = parse_args(config, argv)
    if args.config != 'dlvideo.ini':
        config = Config(config=args.config, script=script)
        args = parse_args(config, argv)
    log = util.get_logger(logfile=config.log, level=config.log_level)
    config.dl_method = args.dl_method
    config.out_dir = args.out_dir
    config.format = args.format
    return args, config, log
