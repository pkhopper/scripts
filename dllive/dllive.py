#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
import urllib
import urllib2
import Queue
from io import BytesIO
from time import sleep
from socket import timeout as _socket_timeout

from vavava import util as _util
from vavava.threadutil import ThreadBase
from vavava.httputil import HttpUtil, HttpDownloadClipHandler
from miniaxel.miniaxel import DownloadUrl, MiniAxelWorkShop

_util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class M3u8Stream(ThreadBase):

    def __init__(self, tmin=10, tmax=20, proxy=None, log=None):
        ThreadBase.__init__(self, log=log)
        self.__oldurls = dict()
        self.__urlwks_q = Queue.Queue()
        self.__axel = MiniAxelWorkShop(tmin=tmin, tmax=tmax, log=log)
        self.__http = HttpUtil()
        if proxy:
            self.__http.set_proxy(proxy)

    def start_dl(self, url, fp, npf):
        """
        start to download live stream spicified by url and write to fp
        @param npf: download url stream by n parts per file
        """
        self.index_url = url
        self.__ostream = fp
        self.__npf = npf
        self.start()

    def run(self):
        try:
            self.__axel.start()
            self.__loop()
        except:
            raise
        finally:
            self.log.debug('[M3u8Stream] stop')
            if not self.__urlwks_q.empty():
                wk = self.__urlwks_q.get()
                wk.cleanUp()
            self.__axel.setToStop()
            self.__axel.join()

    def __loop(self):
        last_index_at = 0
        curr_urlwk = None
        stream_len = 0
        buff_stream_len = 0
        targetduration = 2
        while not self.isSetToStop():
            start_at = time.time()
            if last_index_at + 10 < start_at:
                self.log.debug('[M3u8Stream] try get new clips')
                last_index_at = start_at
                urls, targetduration = self.__get_curr_index()
                for url in urls:
                    if url not in self.__oldurls:
                        memfile = BytesIO()
                        memfile.read = memfile.getvalue
                        urlwork = DownloadUrl(url, out=memfile, n=self.__npf, log=self.log)
                        self.__urlwks_q.put(urlwork)
                        self.__oldurls[url] = True
                        stream_len += targetduration
                        self.log.debug('[M3u8Stream] add a urlwork, %s', url)

            if not curr_urlwk and not self.__urlwks_q.empty():
                curr_urlwk = self.__urlwks_q.get()
                self.__axel.addUrlWork(curr_urlwk)
                self.log.debug('[M3u8Stream] working on a new urlwork, %s', curr_urlwk.url)

            if not curr_urlwk:
                # self.log.debug('[M3u8Stream] idel')
                pass
            elif curr_urlwk.isArchived():
                self.log.debug('[M3u8Stream] archive a urlwork, %s', curr_urlwk.url)
                self.__ostream.write(curr_urlwk.out.read())
                curr_urlwk.out.close()
                curr_urlwk.cleanUp()
                curr_urlwk = None
                buff_stream_len += targetduration
                self.log.info('[M3u8Stream] %d/%d', buff_stream_len, stream_len)
            elif curr_urlwk.isErrorHappen():
                self.log.error('[M3u8Stream] urlwork error: %s', curr_urlwk.url)
                curr_urlwk.cleanUp()
                curr_urlwk = None
                raise

            duration = time.time() - start_at
            if duration < 1:
                sleep(1)

    def __get_curr_index(self):
        try:
            clips = []
            targetduration = 2
            url_base = M3u8Stream.host_filter(self.index_url)
            m3u8 = self.__http.get(self.index_url)
            urls = m3u8.splitlines(False)
            for url in urls:
                url = url.strip(' \n')
                if url.strip() == '':
                    continue
                elif not url.startswith('#'):
                    # self.log.debug('m3u8InerUrl ==> %s', url)
                    if not url.startswith('http'):
                        url = urllib.basejoin(url_base, url)
                    if url.endswith('.m3u8'):
                        return self.__get_curr_index()
                    clips.append(url)
                elif url.lower().find('targetduration') > 0:
                    targetduration = int(url.split(':')[1])
                    self.log.debug('targetduration=%d', targetduration)
            return clips, targetduration
        except urllib2.URLError:
            self.log.debug('network not working')
        except _socket_timeout:
            self.log.debug('connection timeout')
        except:
            raise

    @staticmethod
    def host_filter(url):
        if url.find('ifeng.com') > 0:
            return re.match('(^http[s]?://[^/?]*/)', url).group(0)
        else:
            return re.match('(^http[s]?://.*/)', url).group(0)


class ClipDownloader(ThreadBase):

    def __init__(self, url, fp, duration=None):
        ThreadBase.__init__(self)
        self.url = url
        self.fp = fp
        self.dl_handler = None

    def terminate_dl(self):
        if self.dl_handler:
            self.dl_handler.stop_dl()
            self.dl_handler.wait_stop()
        self.setToStop()
        self.join()

    def run(self):
        try:
            self.dl_handler = HttpDownloadClipHandler(fp=self.fp)
        except:
            if self.dl_handler:
                self.dl_handler.stop_dl()
                self.dl_handler.wait_stop()
            raise


class DownloadLiveStream:
    def __init__(self, proxy=None, log=None):
        self.outfile = None
        self.duration = None
        self.log = log
        self.__m3u8 = M3u8Stream(proxy=proxy,log=log)
        self.__dl_handler = None

    def recode(self, url, duration=None, outpath='./', npf=3):
        assert duration is None or duration > 0
        self.url = url
        self.duration = duration
        self.outpath = outpath
        _util.assure_path(self.outpath)
        self.npf = npf
        name = '%s.%s.ts' % (_util.get_time_string(), hash(url))
        self.outfile = pjoin(outpath, name)
        self.log.info("|=> begin: %s", self.url)
        if self.duration:
            self.log.info("|=>duration: %d", self.duration)
        self.log.info("|=> output: %s", self.outfile)

        start_at = time.time()
        try:
            with open(self.outfile, 'wb') as fp:
                self.__loop(fp=fp)
        except:
            raise
        finally:
            if self.__dl_handler:
                self.__dl_handler.terminate_dl()
            if self.__m3u8.isAlive():
                self.__m3u8.setToStop()
            self.__m3u8.join()
        self.log.info("|=> end: total=%.2fs, out=%s", time.time() - start_at, self.outfile)

    def __loop(self, fp):
        if self.url.find('m3u8') > 0 or DownloadLiveStream.__is_url_file(self.url):
            self.__m3u8.start_dl(url=self.url, fp=fp, npf=self.npf)
        else:
            self.__dl_handler = ClipDownloader(self.url, fp)
            self.__dl_handler.start()
        start_at = time.time()
        stop_at = 0
        if self.duration:
            stop_at = start_at + self.duration
        # self.log.info('duration=%d, start=%f, stop=%f', self.duration, start_at, stop_at)
        while True:
            loop_start_at = time.time()
            if self.duration and loop_start_at >= stop_at:
                self.log.info("[DownloadLiveStream] time's up")
                break
            loop_duration = time.time() - loop_start_at
            if loop_duration < 1:
                sleep(1)

    @staticmethod
    def __is_url_file(url):
        import urllib2
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        info = resp.info()
        return info.type.find('url') > 0


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


def main():
    from config import DLLiveConfig
    from sys import argv
    cfg = DLLiveConfig().read_cmdline_config('dllive.ini', __file__, argv)
    log = cfg.log
    dls = DownloadLiveStream(proxy=cfg.proxyaddr, log=log)
    liveurl = cfg.liveurl
    try:
        if cfg.interactive:
            liveurl = interact(cfg)
        elif cfg.favorite:
            for favorite in cfg.favorites:
                if favorite[0] == cfg.favorite:
                    liveurl = favorite[1]
                    break
        elif cfg.channellist:
            script_path = _util.script_path(__file__)
            os.system('python %s/xbmc_5ivdo.py -t 直播 > %s'%(
                script_path, cfg.address_file))
            return
        dls.recode(url=liveurl, duration=cfg.duration, outpath=cfg.outpath, npf=cfg.npf)
    except KeyboardInterrupt:
        print 'stop by user'
        exit(0)
    except Exception as e:
        log.exception(e)

if __name__ == "__main__":
    main()