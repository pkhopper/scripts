#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import sleep as _sleep
from vavava import util
from config import DLVideoConfig
from vavava.threadutil import WorkShop
from miniaxel.miniaxel import ProgressBar
from vaxel import VUrlTask

util.set_default_utf8()
import parsers

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
pexists = os.path.exists
try:
    user_path = os.environ['HOME']
except:
    user_path = "./"
    print("""os.environ['HOME'] not exists, use user_path = "./" """)


default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

def dl_u2b(cfg):
    if  not cfg.urls[0].find("youtube.com/"):
        return False
    if not util.check_cmd(cfg.u2b_cmd):
        raise Exception( 'command not found:%s' %cfg.u2b_cmd)
    cmd = cfg.u2b_cmd
    cmd += r' --proxy "%s"' % cfg.u2b_proxy
    cmd += r' --o "%s"' % cfg.u2b_tiele_format
    cmd += r' --cache-dir "%s"' % cfg.u2b_cache
    cmd += r' %s' % cfg.urls[0]
    print('==> %s', cmd)
    os.system(cmd)

def main(cfg, log):
    if cfg.playlist:
        for url in cfg.urls:
            outpath, cfg.urls = parsers.getPlayListParser(url).info(url)
            cfg.outpath = pjoin(cfg.outpath, outpath)
            util.assure_path(cfg.outpath)
            with open(pjoin(cfg.outpath, 'url.txt'), 'w') as fp:
                fp.writelines([url + "\n\n"])
                for i, clip in enumerate(cfg.urls):
                    fp.writelines(["[%03d] %s\n"%(i, clip)])

    bar = ProgressBar()
    ws = WorkShop(tmin=cfg.tmin, tmax=cfg.tmax, log=log)
    dlvs = []
    for i, url in enumerate(cfg.urls):
        dlvideo = VUrlTask(url, vidfmt=cfg.vidfmt, npf=cfg.npf,
                           outpath=cfg.outpath, bar=bar, log=log)
        dlvs.append(dlvideo)
    try:
        ws.serve()
        ws.addTasks(dlvs)
        while len(dlvs) > 0:
            for i, dlv in enumerate(dlvs):
                if dlv.isArchived() or dlv.isError():
                    del dlvs[i]
            _sleep(1)
    except Exception as e:
        log.exception(e)
    finally:
        ws.setToStop()
        ws.join()


if __name__ == "__main__":
    cfg = DLVideoConfig().read_cmdline_config('dlvideo.ini', __file__, sys.argv)
    log = cfg.log
    try:
        print sys.argv
        if not dl_u2b(cfg):
            main(cfg, log)
        if util.check_cmd('say'):
            os.system(r'say "download finished!!"')
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        log.exception(e)
        if util.check_cmd('say'):
            os.system(r'say "download failed!!"')
        raise


