#!/usr/bin/env python
# coding=utf-8

import os
from vavava.util import script_path as _script_path
from vavava.util import get_logger as _get_logger
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class Config:

    def __init__(self, config='miniaxel.ini'):
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        if os.path.exists(config):
            cfg.read(pabspath(config))
        else:
            cfg.read(pjoin(_script_path(__file__), config))
        self.out_dir = cfg.get('default', 'out_dir')
        self.retrans = cfg.getboolean('default', 'retrans')
        self.tmin = cfg.getint('default', 'tmin')
        self.tmax = cfg.getint('default', 'tmax')
        self.threadnum = cfg.getint('default', 'threadnum')
        self.log_level = cfg.get('default', 'log_level')
        self.log_file = cfg.get('default', 'log_file')
        if cfg.getboolean('proxy', 'enable'):
            self.proxy = cfg.get('proxy', 'addr')
        else:
            self.proxy = None
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


def parse_args(cfg, prog):
    usage = """./mini """
    import argparse
    parser=argparse.ArgumentParser(prog=prog, usage=usage, description='mini axel', version='0.1')
    parser.add_argument('urls', nargs='*', help='urls')
    parser.add_argument('-c', '--config', default='miniaxel.ini')
    parser.add_argument('-r', '--retransmission', action='store_true', default=cfg.retrans)
    parser.add_argument('-o', '--outdir', dest='out_dir', default=cfg.out_dir)
    parser.add_argument('-p', '--proxy', dest='proxy', action='store_true', default=cfg.proxy)
    parser.add_argument('-n', '--threadnum', default=cfg.threadnum)
    args = parser.parse_args()
    return args


def init_args_config(prog):
    cfg = Config()
    args = parse_args(cfg, prog)
    if args.config != 'miniaxel.ini':
        cfg = Config(config=args.config)
        args = parse_args(cfg, prog)
    log = _get_logger(logfile=cfg.log_file, level=cfg.log_level)
    cfg.retrans = args.retransmission
    cfg.out_dir = args.out_dir
    cfg.threadnum = args.threadnum
    log.info('{}'.format(args))
    return args, cfg, log


def test_miniaxel(self):
    from vavava import util
    url = r'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi'
    orig_md5 = r'140c4a7c9735dd3006a877a9acca3c31'
    out_file = r'out_file'
    test_cases = [
        ['mini', '-n', '5', '-r', url],
        ['mini', '-n', '2', '-r', url],
        ['mini', '-n', '1', '-r', url],
        ['mini', '-n', '5', '-r', url],
    ]
    for argv in test_cases:
        try:
            from miniaxel import main as _main
            _main(argv)
            with open(out_file, 'rb') as fp:
                md5 = util.md5_for_file(fp)
            self.assertTrue(orig_md5 == md5)
        except Exception as e:
            print e
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)