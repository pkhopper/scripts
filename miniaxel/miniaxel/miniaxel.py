#!/usr/bin/env python
# coding=utf-8


import os
import sys
import urllib2
from io import BytesIO
from time import time as _time, sleep as _sleep
from threading import Lock as _Lock
from socket import timeout as _socket_timeout
from vavava.httputil import HttpUtil, HttpFetcher
from vavava import util
from vavava import threadutil

util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class UrlTask(threadutil.TaskBase):
    def __init__(self, url, out, npf=1, proxy=None, bar=None, retrans=False,
                 headers=None, log=None, callback=None):
        threadutil.TaskBase.__init__(self, log=log, callback=callback)
        self.url = url
        self.out = out
        self.npf = npf
        self.proxy = proxy
        self.progress_bar = bar
        self.retransmission = retrans
        self.__history_file = None
        self.headers = headers
        self.__file_mutex = _Lock()

    def makeSubWorks(self):
        cur_size = 0
        size = self.__get_content_len(self.url)
        clip_ranges = HttpFetcher.div_file(size, self.npf)

        if isinstance(self.out, file) or isinstance(self.out, BytesIO):
            self.__fp = self.out
            self.retransmission = False
        elif os.path.exists(self.out):
            self.__fp = open(self.out, 'rb+')
        else:
            self.__fp = open(self.out, 'wb')

        if size and self.retransmission:
            self.__history_file = HistoryFile()
            clip_ranges, cur_size = self.__history_file.mk_clips(self.out, clip_ranges, size)

        # can not retransmission
        if clip_ranges is None or size is None or size == 0:
            self.retransmission = False
            self.log.debug('[DownloadUrl] can not retransmission, %s', self.url)
            clip_ranges = [None]
            size = 0

        if self.progress_bar:
            self.progress_bar.set(total_size=size, cur_size=cur_size)

        for clip_range in clip_ranges:
            work = UrlTask.HttpSubWork(
                url=self.url, fp=self.__fp, file_mutex=self.__file_mutex,
                data_range=clip_range, parent=self, proxy=self.proxy, callback=self.__update
            )
            self.subworks.append(work)
        return self.subworks

    def __get_content_len(self, url):
        http = HttpUtil()
        if self.proxy:
            http.set_proxy(self.proxy)
        info = http.head(url)
        if 200 <= info.status < 300:
            if info.msg.dict.has_key('Content-Length'):
                return int(info.getheader('Content-Length'))
        resp = http.get_response(url)
        if 200 <= resp.code < 300:
            # assert resp.has_header('Accept-Ranges')
            length = int(resp.headers.get('Content-Length'))
            resp.close()
            return length

    def __update(self, offset, size):
        if self.progress_bar:
            self.progress_bar.update(size)
        if self.__history_file:
            self.__history_file.update(offset, size=size)

    def display(self, force=False):
        if self.progress_bar:
            self.progress_bar.display(force)

    def cleanup(self):
        if self.progress_bar:
            self.progress_bar.display(force=True)
        if self.retransmission:
            if self.__history_file:
                self.__history_file.cleanup()
        else:
            # del unfinished file
            if not self.isArchived():
                is_external_file = isinstance(self.out, BytesIO) \
                                   or isinstance(self.out, file)
                if not is_external_file:
                    if os.path.exists(self.out):
                        if self.__fp and self.__fp.closed:
                            self.__fp.close()
                        os.remove(self.out)
        threadutil.TaskBase.cleanup(self)

    class HttpSubWork(threadutil.WorkBase):
        def __init__(self, url, fp, data_range, parent, file_mutex=None,
                     proxy=None, callback=None):
            threadutil.WorkBase.__init__(self, parent=parent)
            self.url = url
            self.fp = fp
            self.data_range = data_range
            self.proxy = proxy
            self.file_mutex = file_mutex
            self.__callback = callback
            self.__retry_count = 0
            self.__http_fetcher = HttpFetcher()
            if self.proxy:
                self.__http_fetcher.set_proxy(self.proxy)

        def setToStop(self):
            self.__http_fetcher.setToStop()
            threadutil.WorkBase.setToStop(self)

        def work(self, this_thread, log):
            while not this_thread.isSetStop() and not self.isSetStop():
                try:
                    self.__http_fetcher.fetch(self.url, fp=self.fp, data_range=self.data_range,
                            file_mutex=self.file_mutex, callback=self.__callback)
                    # log.debug('[HttpSubWork] finish, %s', self.url)
                    return
                except _socket_timeout:
                    self.__retry_count += 1
                    start_at = self.__http_fetcher.handler.start_at
                    end_at = self.__http_fetcher.handler.end_at
                    log.debug('[HttpSubWork] timeout(%d-[%d,%d])  %s', self.__retry_count,
                              start_at, end_at, self.url)
                    _sleep(1)
                except urllib2.URLError as e:
                    log.debug('[HttpSubWork] Network not work :( %s', e.message)
                except Exception as e:
                    log.exception(e)
                    raise


class ProgressBar:

    def __init__(self):
        self.mutex = _Lock()
        self.total_size =0
        self.curr_size =0
        self.last_size = 0
        self.last_updat_at = 0
        self.start_at = 0
        self.sub_bar_count = 0

    def set(self, total_size, cur_size):
        with self.mutex:
            self.sub_bar_count += 1
            self.total_size += total_size
            self.curr_size += cur_size
            self.last_updat_at = _time()
            self.last_size = self.curr_size
            if self.start_at == 0:
                self.start_at = self.last_updat_at

    def update(self, data_size):
        with self.mutex:
            self.curr_size += data_size
        self.display()

    def display(self, force=False):
        if self.last_updat_at < 1:
            return
        now = _time()
        duration = now - self.last_updat_at
        if not force and duration < 1:
            # print '*******%d-%d=%d'%(now, self.last_updat, duration)
            return
        percentage = 10.0*self.curr_size/max(self.total_size, 1)
        if duration == 0:
            speed = 0
        else:
            speed = (self.curr_size - self.last_size)/duration
        output_format = '\r[%d][%3.1d%% %5.1dk/s][ %5.1ds/%5.1ds] [%dk/%dk]            '
        if speed > 0:
            output = output_format % (self.sub_bar_count, percentage*10, speed/1024,
                                      now - self.start_at, (self.total_size-self.curr_size)/speed,
                                      self.curr_size/1024, self.total_size/1024)
        else:
            if self.curr_size == 0:
                expect = 0
            else:
                expect = (self.total_size-self.curr_size)*(now-self.start_at)/self.curr_size
            output = output_format % (self.sub_bar_count, percentage*10, 0, now - self.start_at,
                                      expect, self.curr_size/1024, self.total_size/1024)
        sys.stdout.write(output)
        if percentage == 100:
            sys.stdout.write('\n')
        sys.stdout.flush()
        self.last_updat_at = now
        self.last_size = self.curr_size
        # if force and percentage == 10:
        #     print ''


class HistoryFile:
    def __init__(self):
        self.__mutex = _Lock()
        self.txt = None

    def mk_clips(self, target_file, parts, size):
        """ return clips, current_size, is_retransmission
        """
        self.target_file = os.path.abspath(target_file)
        self.txt = self.target_file + '.txt'
        self.buffered = 0
        cur_size = size
        if os.path.exists(self.txt) and os.path.exists(self.target_file):
            self.parts = []
            with open(self.txt, 'r') as fp:
                for num in fp.read().split('|'):
                    if num.strip() != '':
                        (a, b) = num.split(',')
                        a, b = int(a), int(b)
                        if a <= b:
                            cur_size -= b - a + 1
                            self.parts.append((a, b))
            return self.parts, cur_size
        else:
            if parts is None:
                self.parts = [(0, size - 1)]
            else:
                self.parts = parts
            with open(self.txt, 'w') as fp:
                for clip in self.parts:
                    fp.write('%d,%d|' % clip)
            return parts, 0

    def update(self, offset, size):
        assert size > 0 and offset >=0
        with self.__mutex:
            self.buffered += size
            for i in range(len(self.parts)):
                a, b = self.parts[i]
                if a <= offset <= b:
                    if size <= b - a + 1:
                        self.parts[i] = (a + size, b)
                    else:
                        assert size <= b - a + 1
                    break

    def update_file(self, force=False):
        if not force and self.buffered < 1048576:  # 1024*1024
            return
        with self.__mutex:
            str = ''
            self.buffered = 0
            for (a, b) in self.parts:
                if a < b + 1:
                    str += '%d,%d|' % (a, b)
                else:
                    assert a <= (b + 1)
        with open(self.txt, 'w') as fp:
            fp.write(str)

    def cleanup(self):
        with self.__mutex:
            for (a, b) in self.parts:
                if a < b + 1:
                    self.update_file(force=True)
            if self.txt:
                if os.path.exists(self.txt):
                    os.remove(self.txt)

