#!/usr/bin/env python
# coding=utf-8

import os
import sys

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class Config:
    def __init__(self, config=None):
        if os.path.islink(__file__):
            script_dir = pdirname(pabspath(os.readlink(__file__)))
        else:
            script_dir = pdirname(pabspath(__file__))
        config_file = config
        if config_file:
            config_file = pabspath(config_file)
        else:
            config_file = pjoin(script_dir, 'config.ini')
        import ConfigParser

        cfg = ConfigParser.ConfigParser()
        cfg.read(config_file)
        self.out_dir = cfg.get('default', 'out_dir')
        self.log = cfg.get('default', 'log')
        self.log_level = cfg.get('default', 'log_level')
        lvlconvert = {
            'critical': 50,
            'fatal': 50,
            'error': 40,
            'warning': 30,
            'warn': 30,
            'info': 20,
            'debug': 10,
            'notset': 0
        }
        if self.log_level:
            self.log_level = lvlconvert[self.log_level.strip().lower()]


config = None
log = None

# 

def parse_args():
    usage = """./cmd [-c config][-o out_put_path]"""
    import argparse

    parser = argparse.ArgumentParser(usage=usage, description='', version='0.1')
    parser.add_argument('-c', '--config', default='config.ini')
    parser.add_argument('-o', '--out-path', dest='out_dir', default=config.out_dir)
    args = parser.parse_args()
    return args


def init_args_config():
    config = Config()
    args = parse_args()
    if args.config != 'config.ini':
        config = Config(config=args.config)
        args = parse_args()
    log = util.get_logger(logfile=config.log, level=config.log_level)
    return args, config, log


def main():
    global log
    global config
    args, config, log = init_args_config()
    pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
