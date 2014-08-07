#!/usr/bin/env python
# coding=utf-8

import os
import sys
import config
from vavava import util
from vavava.threadutil import WorkShop
from miniaxel.miniaxel import ProgressBar, UrlTask


util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

test_urls = {
        'dd3322be6b143c6a842acdb4bb5e9f60': 'http://localhost/w/dl/20140728233100.ts',
        # '0d851220f47e7aed4615aebbd5cd2c7a': 'http://localhost/w/dl/test.jpg',
        # '1c9d9fc9b01b4d5d1943b92f23b0e38e': 'http://localhost/w/dl/mysql-connector-java-gpl-5.1.31.msi',
        # '140c4a7c9735dd3006a877a9acca3c31': 'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi',
        # 'asdf': 'http://vavava.baoyibj.com/chaguan/'
}

def fTestFunc(axel, bar, url, md5, npf, log):
    name = 'fTestFunc.%d' % npf
    def archive_callback(wk):
        if not wk.isArchived():
            log.error('[fTestFunc] wk not archive')
            return
        with open(name, 'rb') as fp:
            newmd5 = util.md5_for_file(fp)
        os.remove(name)
        if md5 != newmd5:
            log.error('[fTestFunc] md5 not match, n={}, {} ({})'.format(npf, newmd5, md5))
        else:
            log.info('[fTestFunc] n=%d', npf)
        return
    urltask = UrlTask(url, out=name, npf=npf, bar=bar,
                      retrans=True, callback=archive_callback)
    axel.addTask(urltask)

def mTestFunc(axel, bar, url, md5, npf, log):
    from io import BytesIO
    fp = BytesIO()
    name = 'mTestFunc.%d' % npf
    def archive_callback(wk):
        if not wk.isArchived():
            log.error('[mTestFunc] wk not archive')
            return
        with open(name, 'wb') as ff:
            ff.write(fp.getvalue())
        with open(name, 'rb') as ff:
            newmd5 = util.md5_for_file(ff)
        os.remove(name)
        if md5 != newmd5:
            log.error('[mTestFunc] md5 not match, n={}, {}'.format(npf, newmd5))
        else:
            log.info('[mTestFunc] n=%d', npf)
        return
    urltask = UrlTask(url, out=fp, npf=npf, bar=bar,
                      retrans=True, callback=archive_callback)
    axel.addTask(urltask)

def mainTest(axel, bar, log):
    cmd = '1,2,3,4,5,6'# raw_input('n=')
    for n in cmd.split(','):
        n = int(n)
        for md5, url in test_urls.items():
            fTestFunc(axel, bar, url, md5, n, log)
            # mTestFunc(axel, url, md5, n, log)
            log.debug('add a test work: %s,%s,%d', url, md5, n)

def interface(cmd):
    if cmd.startswith('http'):
        return None, cmd
    name, url = cmd.split(',')
    return name, url

def usage():
    return """
    q --> quit
    t --> tset
    h --> help
    """


def find_name(url):
    u1 = url.split('?')[0]
    if u1.rfind('/') == len(u1) -1:
        u1 = u1[:-1]
    return u1[u1.rfind('/')+1:]


def main(argv):
    cfg = config.MiniAxelConfig()
    cfg.read_cmdline_config('miniaxel.ini', script=__file__, argv=sys.argv)
    log = cfg.log
    bar = ProgressBar()
    axel = WorkShop(tmin=cfg.tmin, tmax=cfg.tmax, log=log)
    try:
        if not axel.serve(timeout=3):
            raise ValueError('server not started')
        if hasattr(cfg, 'urls'):
            for url in cfg.urls:
                log.info('add %s', url)
                name = pjoin(cfg.outpath, find_name(url))
                urltask = UrlTask(url, out=name, npf=cfg.npf, bar=bar, retrans=True, log=cfg.log)
                axel.addTask(urltask)
        while True:
            cmd = raw_input('>>')
            if cmd in ('q'):
                break
            elif cmd in ('h'):
                print usage()
            elif cmd in('test'):
                mainTest(axel, bar, log)
            else:
                name, url = interface(cmd)
                if name:
                    name = pjoin(cfg.outpath, name)
                else:
                    name = pjoin(cfg.outpath, find_name(url))
                urltask = UrlTask(url, out=name, npf=cfg.npf, bar=bar, retrans=True, log=cfg.log)
                axel.addTask(urltask)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        log.exception(e)
        raise
    finally:
        axel.setToStop()
        axel.join()


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
