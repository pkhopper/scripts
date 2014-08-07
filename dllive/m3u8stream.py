#!/usr/bin/env python
# coding=utf-8

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
from vavava.httputil import HttpUtil
from miniaxel.miniaxel import UrlTask, ProgressBar

_util.set_default_utf8()


class M3u8Stream(ThreadBase):
    def __init__(self, axel, proxy=None, log=None):
        ThreadBase.__init__(self, log=log)
        self.__oldurls = dict()
        self.__urltsks_q = Queue.Queue()
        self.__axel = axel
        self.__http = HttpUtil()
        self.__progress_bar = ProgressBar()
        if proxy:
            self.__http.set_proxy(proxy)

    def recode(self, url, duration, fp, npf, freq=10, detach=False):
        """ @param npf: download url stream by n parts per file """
        self.duration = duration
        self.m3u8url = url
        self.__ostream = fp
        self.__npf = npf
        self.__freq = freq
        if detach:
            self.start()
        else:
            self.run()

    def run(self):
        try:
            self.__loop()
        except:
            raise
        finally:
            if not self.__urltsks_q.empty():
                wk = self.__urltsks_q.get()
                wk.cleanup()
            self.log.debug('[M3u8Stream] stop')

    def __loop(self):
        last_index_at = 0
        buff_stream_len = 0
        targetduration = 2
        start_at = time.time()
        stop_at = 0
        if self.duration:
            stop_at = start_at + self.duration

        curr_tsk = None
        while not self.isSetStop():
            start_at = time.time()
            self.__progress_bar.display()

            if self.duration and start_at >= stop_at:
                self.log.info("[DownloadLiveStream] time's up")
                break

            # get index page every 10s
            if last_index_at + self.__freq < start_at:
                last_index_at = start_at
                self.__get_new_clip()

            # append to stream; handle error; get a new clip
            if curr_tsk:
                if curr_tsk.isArchived():
                    self.log.debug('[M3u8Stream] merge clip, %s', curr_tsk.url)
                    self.__ostream.write(curr_tsk.out.read())
                    curr_tsk.out.close()
                    curr_tsk.cleanup()
                    curr_tsk = None
                    buff_stream_len += targetduration
                elif curr_tsk.isError():
                    self.log.error('[M3u8Stream] error: %s', curr_tsk.url)
                    curr_tsk.cleanup()
                    curr_tsk = None
                    raise
            elif not self.__urltsks_q.empty():
                curr_tsk = self.__urltsks_q.get()
                self.log.debug('[M3u8Stream] new clip, %s', curr_tsk.url)

            duration = time.time() - start_at
            if duration < 1:
                sleep(1)

    def __get_new_clip(self):
        urls, targetduration = self.__get_curr_index()
        for url in urls:
            if url not in self.__oldurls:
                memfile = BytesIO()
                memfile.read = memfile.getvalue
                urltask = UrlTask(url, out=memfile, npf=self.__npf,
                                  bar=self.__progress_bar, log=self.log)
                self.__oldurls[url] = True
                self.__axel.addTask(urltask)
                self.__urltsks_q.put(urltask)

    def __get_curr_index(self, n=3):
        urls = []
        targetduration = 0
        try:
            url_base = M3u8Stream.host_filter(self.m3u8url)
            m3u8 = self.__http.get(self.m3u8url)
            uris = m3u8.splitlines(False)
            uris = [uri.strip(' \n') for uri in uris if uri.strip(' \n') != '']
            tags = [uri for uri in uris if uri.startswith('#')]
            urls = [url for url in uris if not url.startswith('#')]
            if not urls[0].startswith('http'):
                urls = [urllib.basejoin(url_base, url) for url in urls]
            for tag in tags:
                if tag.lower().find('targetduration') > 0:
                    targetduration = int(tag.split(':')[1])
                    self.log.debug('targetduration=%d', targetduration)
                    break
            if urls[0].endswith('.m3u8'):
                self.m3u8url = urls[-1:][0]
                return self.__get_curr_index()
        except urllib2.URLError as e:
            self.log.warn('network not working: %s', e.message)
        except _socket_timeout:
            self.log.warn('connection timeout')
        except:
            raise
        return urls, targetduration

    @staticmethod
    def host_filter(url):
        if url.find('ifeng.com') > 0:
            return re.match('(^http[s]?://[^/?]*/)', url).group(0)
        else:
            return re.match('(^http[s]?://.*/)', url).group(0)


# if __name__ == "__main__":
#     main()