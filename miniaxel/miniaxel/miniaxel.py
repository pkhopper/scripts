#!/usr/bin/env python
# coding=utf-8


import os
import sys
import urllib2
import Queue
from io import BytesIO
from time import time as _time, sleep as _sleep
from threading import Event as _Event
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


class DownloadUrl:

    def __init__(self, url, out, n=1, proxy=None, bar=None, retrans=False,
                 headers=None, archive_callback=None, log=None):
        self.url = url
        self.out = out
        self.n = n
        self.proxy = proxy
        self.progress_bar = bar
        self.retransmission = retrans
        self.__history_file = None
        self.headers = headers
        self.archive_callback = archive_callback
        self.log = log

        self.__subworks = []
        self.__err_ev = _Event()
        self.__file_mutex = _Lock()
        # self.__err_ev.clear()
        # 0/1/2/3 init/processing/finish/error
        self.__status = 0

    def __get_content_len(self, url):
        http = HttpUtil()
        if self.proxy:
            http.set_proxy(self.proxy)
        info = http.head(url)
        if 200 <= info.status < 300:
            return int(info.getheader('Content-Length'))
        else:
            resp = http.get_response(url)
            if 200 <= resp.code < 300:
                # assert resp.has_header('Accept-Ranges')
                length = int(resp.headers.get('Content-Length'))
                resp.close()
                return length

    def makeSubWorks(self):
        assert self.__status == 0
        self.__status = 1
        self.__err_ev.clear()
        cur_size = 0
        size = self.__get_content_len(self.url)
        clip_ranges = HttpFetcher.div_file(size, self.n)

        if isinstance(self.out, file) or isinstance(self.out, BytesIO):
            self.__fp = self.out
            self.retransmission = False
        elif os.path.exists(self.out):
            self.__fp = open(self.out, 'rb+')
        else:
            self.__fp = open(self.out, 'wb')

        if size and self.retransmission:
            self.retransmission = False
            self.__history_file = HistoryFile()
            clip_ranges, cur_size = self.__history_file.mk_clips(self.out, clip_ranges, size)

        # can not retransmission
        if clip_ranges is None or size is None or size == 0:
            self.log.debug('[DownloadUrl] can not retransmission, %s', self.url)
            clip_ranges = [None]
            size = 0

        if self.progress_bar:
            self.progress_bar.set(total_size=size, cur_size=cur_size)

        self.__subworks = []
        for clip_range in clip_ranges:
            work = DownloadUrl.HttpDLSubWork(
                url=self.url, fp=self.__fp, file_mutex=self.__file_mutex,
                range=clip_range, parent=self, proxy=self.proxy, callback=self.update
            )
            self.__subworks.append(work)
            self.__status = 2
        return self.__subworks

    def isArchived(self):
        if self.__status < 2 or self.isErrorHappen():
            return False
        for work in self.__subworks:
            if work.isProcessing():
                return False
        return True

    def setError(self):
        self.__err_ev.set()

    def isErrorHappen(self):
        return self.__err_ev.isSet()

    def setStop(self):
        for work in self.__subworks:
            work.setStop()

    def wait(self):
        for work in self.__subworks:
            work.wait()

    def update(self, offset, size):
        if self.progress_bar:
            self.progress_bar.update(size)
        if self.__history_file:
            self.__history_file.update(offset, size=size)

    def display(self, force=False):
        if self.progress_bar:
            self.progress_bar.display(force)

    def cleanUp(self):
        if self.progress_bar:
            self.progress_bar.display(force=True)
        if self.retransmission:
            if self.__history_file:
                self.__history_file.cleanUp()
        else:
            # del unfinished file
            if not self.isArchived():
                is_external_file = isinstance(self.out, BytesIO) or isinstance(self.out, file)
                if not is_external_file:
                    if os.path.exists(self.out):
                        if self.__fp and self.__fp.closed:
                            self.__fp.close()
                        os.remove(self.out)
        if self.archive_callback:
            self.archive_callback(self)

    class HttpDLSubWork(threadutil.WorkBase):

        def __init__(self, url, fp, range, parent, file_mutex=None,
                     proxy=None, callback=None):
            threadutil.WorkBase.__init__(self)
            self.url = url
            self.fp = fp
            self.range = range
            self.proxy = proxy
            self.file_mutex = file_mutex
            self.parent = parent
            self.__callback = callback
            self.__retry_count = 0
            self.__http_fetcher = HttpFetcher()
            if self.proxy:
                self.__http_fetcher.set_proxy(self.proxy)

        def setStop(self):
            threadutil.WorkBase.setStop(self)
            self.__http_fetcher.setStop()

        def work(self, this_thread, log):
            while not this_thread.isSetToStop() and not self.isSetStop():
                try:
                    self.__http_fetcher.fetch(self.url, fp=self.fp, range=self.range,
                            file_mutex=self.file_mutex, callback=self.__callback)
                    return
                except _socket_timeout:
                    self.__retry_count += 1
                    start_at = self.__http_fetcher.handler.start_at
                    end_at = self.__http_fetcher.handler.end_at
                    log.debug('[HttpDLSubWork] timeout(%d-[%d,%d])  %s', self.__retry_count,
                              start_at, end_at, self.url)
                    _sleep(1)
                except urllib2.URLError as e:
                    # log.debug('[HttpDLSubWork] Network not work :(')
                    log.exception(e)
                except Exception as e:
                    if self.parent:
                        self.parent.setError()
                    self.is_err_happen = True
                    raise



class MiniAxelWorkShop(threadutil.ThreadBase):

    def __init__(self, tmin=10, tmax=20, bar=True, retrans=False, log=None):
        threadutil.ThreadBase.__init__(self, log=log)
        if bar:
            self.progress_bar = ProgressBar()
        else:
            self.progress_bar = None
        self.retrans = retrans
        self.__buff_urlwks = Queue.Queue()
        self.__urlwks = []
        self.__ws = threadutil.WorkShop(tmin=tmin, tmax=tmax, log=log)

    def addUrl(self, url, out, headers=None, n=5, archive_callback=None):
        urlwk = DownloadUrl(url, out=out, headers=headers,
                    n=n, retrans=self.retrans, bar=self.progress_bar,
                    archive_callback=archive_callback, log=self.log)
        self.__buff_urlwks.put(urlwk)
        self.log.debug('[axel] add a work: %s', url)


    def addUrlWorks(self, works):
        for wk in works:
            self.addUrlWork(wk)

    def addUrlWork(self, wk):
        assert isinstance(wk, DownloadUrl)
        self.__buff_urlwks.put(wk)
        self.log.debug('[axel] add a work: %s', wk.url)

    def run(self):
        self.log.debug('[axel] start serving')

        self.__ws.serve()
        while not self.isSetToStop():
            start_at = _time()
            try:
                self.__loop()
            except Exception as e:
                self.log.exception(e)
            finally:
                duration = _time() - start_at
                if duration < 0.5:
                    _sleep(0.5)

        for urlwk in self.__urlwks:
            urlwk.setStop()
            urlwk.wait()
            urlwk.cleanUp()
        self.__ws.setStop()
        self.__ws.join()
        self.log.debug('[axel] stop serving')

    def __loop(self):
        self.progress_bar.display()
        if not self.__buff_urlwks.empty():
            urlwk = self.__buff_urlwks.get()
            self.__ws.addWorks(urlwk.makeSubWorks())
            self.__urlwks.append(urlwk)
            self.log.debug('[axel] pop a work: %s', urlwk.url)
        for i, urlwk in enumerate(self.__urlwks):
            urlwk.display()
            if urlwk.isErrorHappen():
                self.log.debug('[axel] work err: %s', urlwk.url)
                urlwk.setStop()
                urlwk.wait()
            if urlwk.isArchived() or urlwk.isErrorHappen():
                urlwk.cleanUp()
                self.log.debug('[axel] work done: %s', urlwk.url)
                del self.__urlwks[i]
                break


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
            return

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
        if force and percentage == 10:
            print ''


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
        assert size > 0
        assert offset >=0
        with self.__mutex:
            self.buffered += size
            for i in xrange(len(self.parts)):
                a, b = self.parts[i]
                if a <= offset <= b:
                    if size <= b - a + 1:
                        self.parts[i] = (a + size, b)
                    else:
                        assert size <= b - a + 1
                    break

    def update_file(self, force=False):
        str = ''
        with self.__mutex:
            if not force and self.buffered < 1000*512:
                return
            self.buffered = 0
            for (a, b) in self.parts:
                if a < b + 1:
                    str += '%d,%d|' % (a, b)
                else:
                    assert a <= (b + 1)
        with open(self.txt, 'w') as fp:
            fp.write(str)

    def cleanUp(self):
        with self.__mutex:
            # for (a, b) in self.parts:
            #     if a < b + 1:
            #         self.update_file(force=True)
            if self.txt:
                if os.path.exists(self.txt):
                    os.remove(self.txt)
