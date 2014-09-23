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
        self.__oldurls = []
        self.__urltsks_q = Queue.Queue()
        self.__axel = axel
        self.__http = HttpUtil()
        self.__progress_bar = ProgressBar()
        if proxy:
            self.__http.set_proxy(proxy)

    def recode(self, url, duration, vfmt, fp, npf, freq=10, detach=False):
        """ @param npf: download url stream by n parts per file
            @param vfmt: live video format """
        self.m3u8url = url
        self.duration = duration
        self.vfmt = int(vfmt) # TODO: ugly conversion
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
            while not self.__urltsks_q.empty():
                self.__urltsks_q.get().cleanup()
            self.log.debug('[M3u8Stream] stop')

    def __loop(self):
        last_clip_at = 0
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
                return

            # get index page every 10s
            if last_clip_at + self.__freq < start_at:
                urls, targetduration = self.__get_curr_m3u8_file(self.m3u8url)
                for url in urls:
                    if url not in self.__oldurls:
                        memfile = BytesIO()
                        memfile.read = memfile.getvalue
                        urltask = UrlTask(url, out=memfile, npf=self.__npf,
                                          bar=self.__progress_bar, log=self.log)
                        self.__oldurls.append(url)
                        self.__axel.addTask(urltask)
                        self.__urltsks_q.put(urltask)
                if len(self.__oldurls) > 100:
                    self.__oldurls = self.__oldurls[-20:]
                last_clip_at = start_at

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
                    raise
            elif not self.__urltsks_q.empty():
                curr_tsk = self.__urltsks_q.get()

            if time.time() - start_at < 1:
                sleep(1)

    def __get_curr_m3u8_file(self, m3u8url, n=3):
        urls = []
        sub_m3u8s = []
        targetduration = 0
        try:
            m3u8 = self.__http.get(m3u8url)
            for line in m3u8.splitlines(False):
                line = line.strip(' \n')
                if line == '':
                    continue
                if line.startswith('#'):
                    if line.lower().find('targetduration') > 0:
                        targetduration = int(line.split(':')[1])
                        self.log.debug('[M3u8Stream] targetduration=%d', targetduration)
                else:
                    if line.startswith('http'):
                        urls.append(line)
                    else:
                        url = urllib.basejoin(M3u8Stream.host_filter(m3u8url), line)
                        if line.endswith('.m3u8'):
                            sub_m3u8s.append(url)
                        else:
                            urls.append(url)

            sm_len = len(sub_m3u8s)
            if sm_len > 0:
                fmt_index = self.vfmt if self.vfmt < sm_len else sm_len-1
                self.log.debug('[M3u8Stream] use sub m3u8 url: %s', sub_m3u8s[fmt_index])
                return self.__get_curr_m3u8_file(sub_m3u8s[fmt_index])
        except urllib2.URLError as e:
            self.log.warn('[M3u8Stream] network not working: %s', e.message)
        except _socket_timeout:
            self.log.warn('[M3u8Stream] connection timeout')
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