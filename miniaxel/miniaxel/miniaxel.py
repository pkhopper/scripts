#!/usr/bin/env python
# coding=utf-8


import os
import sys
import urllib2
from time import time as _time, sleep as _sleep
from threading import RLock as _RLock
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
    def __init__(self, url, out, npf=1, headers=None, proxy=None,
                 bar=None, retrans=False, callback=None, log=None):
        threadutil.TaskBase.__init__(self, log=log)
        self.url = url
        self.out = out
        self.tmp_file = ''
        self.npf = npf
        self.proxy = proxy
        self.progress_bar = bar
        self.__is_inter_file = isinstance(self.out, str)
        self.retrans = retrans
        self.__history_file = None
        self.headers = headers
        self.__callback = callback

    def makeSubWorks(self):
        curr_size = 0
        size = self.__get_content_len(self.url)
        clip_ranges = HttpFetcher.div_file(size, self.npf)

        if not self.__is_inter_file:
            self.__fp = self.out
            self.retrans = False
        else:
            self.tmp_file = self.out + '!'
            if os.path.exists(self.tmp_file):
                self.__fp = open(self.tmp_file, 'rb+')
            else:
                self.__fp = open(self.tmp_file, 'wb')

        if size and self.retrans:
            self.__history_file = HistoryFile()
            clip_ranges, curr_size = self.__history_file.load(
                self.tmp_file, clip_ranges, size)

        # can not retransmission
        if clip_ranges is None or size is None or size == 0:
            self.retrans = False
            self.log.debug('[DownloadUrl] can not retransmission, %s', self.url)
            clip_ranges = [None]
            size = 0

        if self.progress_bar:
            self.progress_bar.set(total_size=size, curr_size=curr_size)

        subworks = []
        syn_file = util.SynFileContainer(self.__fp)
        for clip_range in clip_ranges:
            work = UrlTask.HttpSubWork(
                url=self.url, fp=syn_file, data_range=clip_range, parent=self,
                headers=self.headers, proxy=self.proxy, callback=self.__update, log=self.log
            )
            subworks.append(work)
        return subworks

    def __get_content_len(self, url):
        http = HttpUtil()
        if self.proxy:
            http.set_proxy(self.proxy)
        info = http.head(url)
        if 200 <= info.status < 300:
            if info.msg.dict.has_key('Content-Length'):
                return int(info.getheader('Content-Length'))
        try:
            resp = http.get_response(url)
        except urllib2.URLError as e:
            self.log.warn('%s \n %s', e.reason, url)
            return 0
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
        if not os.path.exists(self.tmp_file):
            return
        if self.__is_inter_file:
            if not self.__fp.closed:
                self.__fp.close()
            if self.isArchived():
                if not self.retrans or (self.retrans and self.__history_file.isFinished()):
                    os.rename(self.tmp_file, self.out)
            elif not self.retrans:
                os.remove(self.tmp_file)
        if self.__history_file:
            self.__history_file.cleanup()
        if self.progress_bar:
            self.progress_bar.display(force=True)
        if self.__callback:
            self.__callback(self)

    class HttpSubWork(threadutil.WorkBase):
        def __init__(self, url, fp, data_range, parent, headers=None,
                     proxy=None, callback=None, log=None):
            threadutil.WorkBase.__init__(self, parent=parent)
            self.url = url
            self.fp = fp
            self.data_range = data_range
            self.proxy = proxy
            self.headers = headers
            self.__callback = callback
            self.log = log
            self.__retry_count = 0
            self.__http_fetcher = HttpFetcher(log=log)
            if self.proxy:
                self.__http_fetcher.set_proxy(self.proxy)

        def work(self, this_thread, log):
            isSetStop = lambda : this_thread.isSetStop() or self.isSetStop()
            while not isSetStop():
                try:
                    if self.headers:
                        self.__http_fetcher.add_headers(self.headers)
                    self.__http_fetcher.fetch(
                        self.url, fp=self.fp, data_range=self.data_range,
                        isSetStop=isSetStop, callback=self.__callback
                    )
                    return
                except _socket_timeout:
                    self.__retry_count += 1
                    start_at = self.__http_fetcher.handler.start_at
                    end_at = self.__http_fetcher.handler.end_at
                    log.debug('[HttpSubWork] timeout(%d-[%d,%d]) %s', self.__retry_count,
                              start_at, end_at, self.url)
                    _sleep(1)
                except urllib2.URLError as e:
                    log.debug('[HttpSubWork] Network not work :( %s', e.reason)
                    _sleep(1)
                except:
                    raise


class ProgressBar:

    def __init__(self):
        self.mutex = _RLock()
        self.total_size =0
        self.curr_size =0
        self.last_size = 0
        self.last_updat_at = 0
        self.start_at = 0
        self.sub_bar_count = 0
        self.__echo_bak = self.echo

    def set(self, total_size, curr_size):
        with self.mutex:
            self.sub_bar_count += 1
            self.total_size += total_size
            self.curr_size += curr_size
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
        output_format = '[%d][%3.1d%% %5.1dk/s][%2dm%2ds/%2dm%2ds] [%dk/%dk]            '
        if speed > 0:
            past = now - self.start_at
            last = (self.total_size-self.curr_size)/speed
            output = output_format % (self.sub_bar_count, percentage*10, speed/1024,
                                      past/60, past%60, last/60, last%60,
                                      self.curr_size/1024, self.total_size/1024)
        else:
            if self.curr_size == 0:
                expect = 0
                past = 0
            else:
                expect = (self.total_size-self.curr_size)*(now-self.start_at)/self.curr_size
                past = now - self.start_at
            output = output_format % (self.sub_bar_count, percentage*10, 0,
                                      past/60, past%60, expect/60, expect%60,
                                      self.curr_size/1024, self.total_size/1024)
        self.echo(output)
        self.last_updat_at = now
        self.last_size = self.curr_size

    def echo(self, msg):
        sys.stdout.write('\r' + msg)
        # if percentage == 100:
        #     sys.stdout.write('\n')
        sys.stdout.flush()

    def recover_echo(self, caller):
        self.echo = self.__echo_bak

class HistoryFile:
    def __init__(self):
        self.__mutex = _RLock()
        self.hfile = None
        # self.__fp = None

    def load(self, target_file, parts, size):
        """ return clips, current_size, is_retransmission
        """
        self.target = os.path.abspath(target_file)
        self.hfile = self.target + '.cfg'
        self.buffered = 0
        cur_size = size
        if os.path.exists(self.hfile) and os.path.exists(self.target):
            self.parts = []
            with open(self.hfile, 'r') as fp:
                for num in fp.read().split('|'):
                    if num.strip() != '':
                        (a, b) = num.split(',')
                        a, b = int(a), int(b)
                        if a <= b:
                            cur_size -= b - a + 1
                            self.parts.append((a, b))
            # self.__fp = open(self.hfile, 'w')
            self.update_file(force=True)
            return self.parts, cur_size
        else:
            if parts is None:
                self.parts = [(0, size - 1)]
            else:
                self.parts = parts
            # self.__fp = open(self.hfile, 'w')
            self.update_file(force=True)
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
        self.update_file()

    def update_file(self, force=False):
        if not force and self.buffered < 1048576:  # 1024*1024
            return
        with self.__mutex:
            str = ''
            self.buffered = 0
            for (a, b) in self.parts:
                str += '%d,%d|' % (a, b)
            with open(self.hfile, 'w') as fp:
                fp.write(str)
            # TODO: append when write, truncate not work, why??
            # self.__fp.truncate()
            # self.__fp.write(str)
            # self.__fp.flush()

    def isFinished(self):
        with self.__mutex:
            for (a, b) in self.parts:
                if a < b + 1:
                    return False
        return True

    def cleanup(self):
        finished = True
        with self.__mutex:
            for (a, b) in self.parts:
                if a < b + 1:
                    finished = False
            if not finished:
                self.update_file(force=True)
            # if self.hfile:
            #     if not self.__fp.closed:
            #         self.__fp.close()
            if finished and os.path.exists(self.hfile):
                os.remove(self.hfile)


test_urls = {
        'dd3322be6b143c6a842acdb4bb5e9f60': 'http://localhost/w/dl/20140728233100.ts',
        # '0d851220f47e7aed4615aebbd5cd2c7a': 'http://localhost/w/dl/test.jpg'
}

def fTestFunc(axel, bar, url, md5, npf, log):
    # util.assure_path('./tmp')
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
        # else:
        #     log.info('[fTestFunc] n=%d', npf)
        return
    urltask = UrlTask(url, out=name, npf=npf, bar=bar, log=log,
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
    urltask = UrlTask(url, out=fp, npf=npf, bar=bar, log=log,
                      retrans=True, callback=archive_callback)
    axel.addTask(urltask)

def mainTest(axel, bar, log):
    cmd = "1" #'1,2,3,4,5,6'# raw_input('n=')
    for n in cmd.split(','):
        n = int(n)
        for md5, url in test_urls.items():
            fTestFunc(axel, bar, url, md5, n, log)
            # mTestFunc(axel, url, md5, n, log)
            log.debug('add a test work: %s,%s,%d', url, md5, n)

from vavava.threadutil import WorkShop
from vavava.util import get_logger
if __name__ == '__main__':
    log = get_logger()
    bar = ProgressBar()
    axel = WorkShop(tmin=2, tmax=5, log=log)
    try:
        if not axel.serve(timeout=3):
            raise ValueError('server not started')
        mainTest(axel, bar, log)
        while True:
            _sleep(1)
            if axel.allTasksDone():
                if raw_input('again ??') in ('y'):
                    mainTest(axel, bar, log)
                else:
                    break
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        log.exception(e)
        raise
    finally:
        axel.setToStop()
        axel.join()