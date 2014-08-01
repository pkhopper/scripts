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


class Config:
    def __init__(self, config="dllive.ini"):
        # script_dir = _util.script_path(__file__)
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        if os.path.exists(config):
            cfg.read(pabspath(config))
        else:
            cfg.read(pjoin(_util.script_path(__file__), config))
        self.out_dir = cfg.get('default', 'out_dir')
        self.channel = cfg.get('default', 'channel')
        # self.duration = cfg.getint('default', 'duration')
        self.log = cfg.get('default', 'log')
        self.log_level = cfg.get('default', 'log_level')
        self.live_url = cfg.get('default', 'live_url')
        self.pythonpath = cfg.get('environment', 'pythonpath')
        self.address_file = cfg.get('address_file', 'name')
        self.proxy_addr = cfg.get('proxy', 'addr')
        self.proxy_enable = cfg.getboolean('proxy', 'enable')
        self.favorites = cfg.items('favorites')
        lvlconvert = {
            'critical': 50,
            'fatal': 50,
            'error': 40,
            'warning': 30,
            'warn': 30,
            'info': 20,
            'debug': 10,
            'notset': 0
        }
        if self.log_level:
            self.log_level = lvlconvert[self.log_level.strip().lower()]
config = None
log = None


class M3u8Stream(ThreadBase):
    TMP_PATH = '.dllive'

    def __init__(self, log=None):
        ThreadBase.__init__(self, log=log)
        self.__http = HttpUtil(timeout=10)
        self.__old_urls = dict()
        self.__urlworks_queue = Queue.Queue()
        self.__axel = MiniAxelWorkShop(tmin=10, tmax=20, log=log)

    def start_dl(self, url, fp, proxy=None):
        if proxy:
            self.__http.set_proxy({'http': proxy})
        self.index_url = url
        self.__ostream = fp
        self.tmp_path = pjoin(config.out_dir, M3u8Stream.TMP_PATH)
        _util.assure_path(self.tmp_path)
        self.start()

    def run(self):
        try:
            self.__axel.start()
            self.__loop()
        except:
            raise
        finally:
            self.log.debug('[M3u8Stream] stop')
            if not self.__urlworks_queue.empty():
                wk = self.__urlworks_queue.get()
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
                    if url not in self.__old_urls:
                        memfile = BytesIO()
                        memfile.read = memfile.getvalue
                        urlwork = DownloadUrl(url, out=memfile, n=3, log=self.log)
                        self.__urlworks_queue.put(urlwork)
                        self.__old_urls[url] = True
                        stream_len += targetduration
                        self.log.debug('[M3u8Stream] add a urlwork, %s', url)

            if not curr_urlwk and not self.__urlworks_queue.empty():
                curr_urlwk = self.__urlworks_queue.get()
                self.__axel.addUrlWorks([curr_urlwk])
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


class DownloadLiveStream(ThreadBase):

    def __init__(self, log):
        ThreadBase.__init__(self, log=log)
        self.outfile = None
        self.duration = None
        self.__m3u8 = M3u8Stream(log=log)
        self.__dl_handler = None

    def __prepair(self, url, out_dir, duration, proxy):
        assert duration is None or duration > 0
        self.duration = duration
        self.out_dir = out_dir
        self.outfile = pjoin(out_dir, _util.get_time_string() + ".ts")
        self.url = url
        self.proxy = proxy

    def recode_in_this_thread(self, url, out_dir, duration=None, proxy=None):
        self.__prepair(url, out_dir, duration, proxy)
        self.__run_in_caller_thread = True
        self.run()

    def start_recode(self, url, out_dir, duration=None, proxy=None):
        self.__prepair(url, out_dir, duration, proxy)
        self.start()

    def run(self):
        self.log.info("|=> begin: %s", self.url)
        if self.duration:
            self.log.info("|duration: %d", self.duration)
        _util.assure_path(self.out_dir)
        self.log.info("|=> output: %s", self.outfile)
        start_at = time.time()
        try:
            with open(self.outfile, 'wb') as fp:
                self.__loop(fp=fp)
        except:
            pass
        finally:
            if self.__dl_handler:
                self.__dl_handler.terminate_dl()
            if self.__m3u8.isAlive():
                self.__m3u8.setToStop()
            self.__m3u8.join()
        self.log.info("|=> end: total=%.2fs, out=%s", time.time() - start_at, self.outfile)

    def __loop(self, fp):
        if self.url.find('m3u8') > 0 or DownloadLiveStream.__is_url_file(self.url):
            self.__m3u8.start_dl(url=self.url, fp=fp, proxy=self.proxy)
        else:
            self.__dl_handler = ClipDownloader(self.url, fp)
            self.__dl_handler.start()
        start_at = time.time()
        stop_at = 0
        if self.duration:
            stop_at = start_at + self.duration
        # self.log.info('duration=%d, start=%f, stop=%f', self.duration, start_at, stop_at)
        while not self.isSetToStop() or self.__run_in_caller_thread:
            loop_start_at = time.time()
            if self.duration and loop_start_at >= stop_at:
                self.log.info("[DownloadLiveStream] time's up")
                break
            loop_duration = time.time() - loop_start_at
            if loop_duration < 1:
                sleep(1)

    def stopRecode(self):
        if self.isAlive():
            self.setToStop()

    @staticmethod
    def __is_url_file(url):
        import urllib2
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        info = resp.info()
        return info.type.find('url') > 0


def interact(duration, out_dir, address_file, proxy=None):
    log.info('===>interact mode')
    channel = raw_input('channel?')
    with open(address_file, 'r') as fp:
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
    dls = DownloadLiveStream(log=log)
    try:
        dls.start_recode(url=sub_addr[channel_list[channel_id]],
                         out_dir=out_dir, duration=duration, proxy=proxy)
    except:
        raise
    finally:
        dls.setToStop()
        dls.join()

def parse_args(config):
    usage = """./dllive [-i|l][-c config][-o out_put_path][-f favorite][-d duration]"""
    import argparse
    parser=argparse.ArgumentParser(usage=usage, description='download live stream', version='0.1')
    parser.add_argument('-c', '--config', default='dllive.ini')
    parser.add_argument('-d', '--duration', type=float)
    parser.add_argument('-o', '--out-path', dest='out_dir', default=config.out_dir)
    parser.add_argument('-p', '--proxy', dest='proxy', action='store_const', const=True, help='http/https proxy')
    parser.add_argument('-i', '--interactive', action='store_const', dest='interactive', const=True, help='interactive mode.')
    parser.add_argument('-u', '--url', dest='url', help='live stream url')
    parser.add_argument('-f', '--favorite', dest='favorite', help='favorite channel name, define in config file.')
    parser.add_argument('-l', '--channel-list', dest='channellist', action='store_const', const=True, help='update addresses.')
    args = parser.parse_args()
    print args
    return args


def init_args_config():
    config = Config()
    args = parse_args(config)
    if args.config != 'dllive.ini':
        config = Config(config=args.config)
        args = parse_args(config)
    log = _util.get_logger(logfile=config.log, level=config.log_level)
    return args, config, log


def main():
    global log
    global config
    args, config, log = init_args_config()
    log.info('{}'.format(args))
    live_url = config.live_url
    proxy = None
    if args.proxy:
        proxy = config.proxy_addr
    if args.interactive:
        interact(duration=args.duration, out_dir=args.out_dir,
                 address_file=config.address_file, proxy=proxy)
        return
    elif args.channellist:
        script_path = _util.script_path(__file__)
        os.system('python %s/xbmc_5ivdo.py -t 直播 > %s'%(
            script_path, config.address_file))
        return
    elif args.favorite:
        for favorite in config.favorites:
            if favorite[0] == args.favorite:
                live_url = favorite[1]
                break
    elif args.url:
        live_url = args.url

    dls = DownloadLiveStream(log=log)
    try:
        dls.recode_in_this_thread(url=live_url, out_dir=args.out_dir,
                         duration=args.duration, proxy=proxy)
    except Exception as e:
        log.exception(e)
        raise
    # finally:
    #     if not dls.isAlive():
    #         dls.stopRecode()
    #         dls.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
