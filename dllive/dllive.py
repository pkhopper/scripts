#!/usr/bin/env python
# coding=utf-8

import os
import time
from vavava import util as _util
from vavava.httputil import HttpFetcher
from vavava.threadutil import WorkShop
from miniaxel.miniaxel import ProgressBar
from m3u8stream import M3u8Stream

_util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


def __is_url_file(url):
    import urllib2
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    info = resp.info()
    return info.type.find('url') > 0


def recode(url, duration=None, outpath='./',
           npf=3, freq=10, tmin=5, tmax=20, proxy=None, log=None):
    assert duration is None or duration > 0
    name = '%s.%s.ts' % (_util.get_time_string(), hash(url))
    outfile = pjoin(outpath, name)
    log.info("|=> begin: %s", url)
    if duration:
        log.info("|=>duration: %d", duration)
    log.info("|=> output: %s", outfile)

    _util.assure_path(outpath)
    axel = WorkShop(tmin=tmin, tmax=tmax, log=log)
    m3u8 = M3u8Stream(axel=axel, proxy=proxy,log=log)
    fetcher = HttpFetcher()
    start_at = time.time()
    try:
        with open(outfile, 'wb') as fp:
            if url.find('m3u8') > 0 or __is_url_file(url):
                axel.serve()
                m3u8.recode(url=url, duration=duration, fp=fp, npf=npf, freq=cfg.freq)
            else:
                fetcher.fetch(url=url, fp=fp)
        log.info("|=> end: total=%.2fs, out=%s", time.time() - start_at, outfile)
    finally:
        if axel.isAlive():
            axel.setToStop()
            axel.join()


def interact(cfg):
    channel = raw_input('channel?')
    with open(cfg.address_file, 'r') as fp:
        address = fp.readlines()
    sub_addr = dict()
    for addr in address:
        kv = addr.split('#')
        if kv[0].lower().find(channel) > 0:
            sub_addr[kv[0]] = kv[1]
    index = 0
    channel_list = []
    for k, v in sub_addr.items():
        index += 1
        channel_list.append(k)
        print '[%2d] %s  %s'%(index, k, v)
    channel_id = int(raw_input('id? ')) - 1
    return sub_addr[channel_list[channel_id]]


def main(cfg):
    liveurl = cfg.liveurl
    if cfg.interactive:
        liveurl = interact(cfg)
    elif cfg.favorite:
        for f in cfg.favorites:
            if f[0] == cfg.favorite:
                liveurl = f[1]
    elif cfg.channellist:
        spath = _util.script_path(__file__)
        os.system('python %s/xbmc_5ivdo.py -t 直播 > %s'%(spath, cfg.address_file))
        return
    recode(url=liveurl, duration=cfg.duration, outpath=cfg.outpath, npf=cfg.npf,
           freq=cfg.freq, tmin=cfg.tmin, tmax=cfg.tmax, proxy=cfg.proxyaddr, log=cfg.log)


if __name__ == "__main__":
    from config import DLLiveConfig
    from sys import argv
    cfg = DLLiveConfig().read_cmdline_config('dllive.ini', __file__, argv)
    try:
        main(cfg)
    except KeyboardInterrupt:
        print 'stop by user'
        exit(0)
    except Exception as e:
        cfg.log.exception(e)