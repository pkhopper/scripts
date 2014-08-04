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
        self.__urlwks_q = Queue.Queue()
        self.__axel = axel
        self.__http = HttpUtil()
        self.__progress_bar = ProgressBar()
        if proxy:
            self.__http.set_proxy(proxy)

    def recode(self, url, duration, fp, npf, freq=10, detach=False):
        """ @param npf: download url stream by n parts per file """
        self.duration = duration
        self.index_url = url
        self.__ostream = fp
        self.__npf = npf
        self.__freq = freq
        if detach:
            self.start()
        else:
            self.run()

    def run(self):
        try:
            if not self.__axel.isAlive():
                self.log.warn('[M3u8Stream] axel not alive')
                return
            self.__loop()
        except:
            raise
        finally:
            self.log.debug('[M3u8Stream] stop')
            if not self.__urlwks_q.empty():
                wk = self.__urlwks_q.get()
                wk.cleanup()

    def __loop(self):
        last_index_at = 0
        buff_stream_len = 0
        targetduration = 2
        start_at = time.time()
        stop_at = 0
        if self.duration:
            stop_at = start_at + self.duration

        curr_urlwk = None
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
            if curr_urlwk:
                if curr_urlwk.isArchived():
                    self.log.debug('[M3u8Stream] merge clip, %s', curr_urlwk.url)
                    self.__ostream.write(curr_urlwk.out.read())
                    curr_urlwk.out.close()
                    curr_urlwk.cleanup()
                    curr_urlwk = None
                    buff_stream_len += targetduration
                elif curr_urlwk.isErrorHappen():
                    self.log.error('[M3u8Stream] error: %s', curr_urlwk.url)
                    curr_urlwk.cleanup()
                    curr_urlwk = None
                    raise
            elif not self.__urlwks_q.empty():
                curr_urlwk = self.__urlwks_q.get()
                self.log.debug('[M3u8Stream] new clip, %s', curr_urlwk.url)

            duration = time.time() - start_at
            if duration < 1:
                sleep(1)

    def __get_new_clip(self):
        urls, targetduration = self.__get_curr_index()
        for url in urls:
            if url not in self.__oldurls:
                memfile = BytesIO()
                memfile.read = memfile.getvalue
                urlwork = UrlTask(url, out=memfile, npf=self.__npf,
                                  bar=self.__progress_bar, log=self.log)
                self.__urlwks_q.put(urlwork)
                self.__oldurls[url] = True
                self.__axel.addUrlWork(urlwork)

    def __get_curr_index(self):
        clips = []
        targetduration = 0
        try:
            url_base = M3u8Stream.host_filter(self.index_url)
            m3u8 = self.__http.get(self.index_url)
            urls = m3u8.splitlines(False)
            for url in urls:
                url = url.strip(' \n')
                if url.strip() == '':
                    continue
                elif not url.startswith('#'):
                    if not url.startswith('http'):
                        url = urllib.basejoin(url_base, url)
                    if url.endswith('.m3u8'):
                        return self.__get_curr_index()
                    clips.append(url)
                elif url.lower().find('targetduration') > 0:
                    targetduration = int(url.split(':')[1])
                    self.log.debug('targetduration=%d', targetduration)
        except urllib2.URLError as e:
            self.log.warn('network not working: %s', e.message)
        except _socket_timeout:
            self.log.warn('connection timeout')
        except:
            raise
        return clips, targetduration

    @staticmethod
    def host_filter(url):
        if url.find('ifeng.com') > 0:
            return re.match('(^http[s]?://[^/?]*/)', url).group(0)
        else:
            return re.match('(^http[s]?://.*/)', url).group(0)


# if __name__ == "__main__":
#     main()