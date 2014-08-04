#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import sleep as _sleep
from vavava import util
from config import DLVideoConfig
from miniaxel.miniaxel import MiniAxelWorkShop, ProgressBar
from vaxel import VAxel, DLVWork

util.set_default_utf8()
import parsers

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
pexists = os.path.exists
user_path = os.environ['HOME']


default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'


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

    axel = MiniAxelWorkShop(tmin=cfg.tmin, tmax=cfg.tmax, bar=ProgressBar(), retrans=True, log=log)
    vaxel = VAxel(axel=axel, log=log)

    dlvs = []
    for i, url in enumerate(cfg.urls):
        dlvideo = DLVWork(url, vidfmt=cfg.format, npf=cfg.npf,
                              outpath=cfg.outpath, axel=axel, id=i, log=log)
        dlvs.append(dlvideo)
    try:
        axel.start()
        vaxel.serve()
        vaxel.addWorks(dlvs)
        while len(dlvs) > 0:
            _sleep(1)
            for i, wk in enumerate(dlvs):
                if not wk.isProcessing():
                    del dlvs
            print sys.stdin.readline()
    except:
        pass
    finally:
        axel.setToStop()
        axel.join()
        vaxel.setToStop()
        vaxel.join()

def interface():
    i = 0
    cmd = raw_input(i)


if __name__ == "__main__":
    cfg = DLVideoConfig().read_cmdline_config('dlvideo.ini', __file__, sys.argv)
    log = cfg.log
    try:
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


