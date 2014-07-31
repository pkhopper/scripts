#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
from miniaxel.miniaxel import MiniAxelWorkShop
import config

util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


def main(argv):
    args, cfg, log = config.init_args_config(argv)
    axel = MiniAxelWorkShop(tmin=cfg.tmin, tmax=cfg.tmax, bar=True, retrans=True, log=log)
    try:
        axel.start()
        for url in args.urls:
            log.info('add %s', url)
            name = pjoin(cfg.out_dir, find_name(url))
            axel.addUrl(url, out_name=name, n=cfg.threadnum)
        while True:
            cmd = raw_input('>>')
            if cmd in ('q'):
                break
            elif cmd in('test'):
                url = r'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi'
                name = pjoin(cfg.out_dir, find_name(url))
                axel.addUrl(url, out_name=name, n=cfg.threadnum)
            else:
                url = cmd
                name = pjoin(cfg.out_dir, find_name(url))
                axel.addUrl(url, out_name=name, n=cfg.threadnum)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        log.exception(e)
        raise
    finally:
        axel.setToStop()
        axel.join()


def find_name(url):
    u1 = url.split('?')[0]
    if u1.rfind('/') == len(u1) -1:
        u1 = u1[:-1]
    return u1[u1.rfind('/')+1:]


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
