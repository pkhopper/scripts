#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
import urllib
import urllib2
from time import sleep

from vavava.httputil import HttpUtil
from vavava.httputil import MiniAxel
from vavava.httputil import HttpDownloadClipHandler
from vavava import util
from vavava.threadutil import ThreadBase, ThreadManager

util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class Config:
    def __init__(self, config="config.ini"):
        # script_dir = util.script_path(__file__)
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        if os.path.exists(config):
            cfg.read(pabspath(config))
        else:
            cfg.read(pjoin(util.script_path(__file__), config))
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


def get_channel_url(name, addr_file):
    urls = []
    with open(addr_file, 'r') as fp:
        channels = fp.readlines()
    for channel in channels:
        info = channel.split('#')
        if len(info) < 2:
            continue
        channel_name, url = info[0], info[1]
        if channel_name.lower().find(name) > 0:
            urls.append(url)
    return urls


def filter_host(url):
    if url.find('ifeng.com') > 0:
        return re.match('(^http[s]?://[^/?]*/)', url).group(0)
    else:
        return re.match('(^http[s]?://.*/)', url).group(0)


class M3u8:
    TMP_PATH = '.dllive'

    def __init__(self, http, log):
        self.http = http
        self.log = log
        self.old_urls = dict()
        self.mgr = None
        self.single_dl_handle = None

    def terminate_dl(self, timeout=None):
        if self.mgr:
            self.mgr.stopAll()
            self.mgr.joinAll(timeout=timeout)
        if self.single_dl_handle:
            self.single_dl_handle.stop()
            self.single_dl_handle.join(timeout=timeout)

    def dl_stream(self, url, url_base, fp):
        start_time = time.time()
        total_server = 0
        # stop_time = duration + start_time
        while True:
            before = time.time()
            count, total, targetduration = self.__dl_stream(url, url_base, output_fp=fp)
            after = time.time()
            curr_local = after - before   # time_transfer
            curr_server = count * targetduration
            curr_buffered = curr_server - curr_local
            total_server += curr_server
            total_local = after - start_time
            total_buffered = total_server - total_local
            # T=total;C=current;
            self.log.debug('CURR:%.2f/%.2f(%.2f);TOTAL:%.2f/%.2f(%.2f);DURATION:%d;COUNT:%d',
                      curr_local, curr_server, curr_buffered, total_local,
                      total_server, total_buffered, targetduration, count)
            # if duration > 0 and stop_time - after < max(curr_buffered, 0.01):
            #     log.debug(r"===> time's up.")
            #     break
            need_wait = curr_buffered > targetduration and total_buffered > targetduration
            if count == 0 or need_wait:
                wait = min(10, targetduration)
                self.log.debug('sleep(%d)', wait)
                sleep(wait)

    def __get_curr_index(self, url, url_base=None):
        lines = []
        targetduration = 2
        if url_base is None:
            url_base = re.match('(^http[s]?://.*/)', url).group(0)
        m3u8 = self.http.get(url)
        urls = m3u8.splitlines(False)
        for url in urls:
            if url.strip() == '':
                continue
            elif not url.startswith('#'):
                self.log.debug('m3u8InerUrl ==> %s', url)
                if not url.startswith('http'):
                    url = urllib.basejoin(url_base, url)
                if url.endswith('.m3u8'):
                    return self.__get_curr_index(url, url_base)
                lines.append(url)
            elif url.lower().find('targetduration') > 0:
                targetduration = int(url.split(':')[1])
                self.log.debug('targetduration=%d', targetduration)
        return lines, targetduration

    def __dl_stream(self, url, url_base, output_fp):
        self.mgr = ThreadManager()
        name_index = count = 0
        clips = []
        tmp_path = pjoin(config.out_dir, M3u8.TMP_PATH)
        util.assure_path(tmp_path)
        urls, targetduration = self.__get_curr_index(url, url_base)
        for url in urls:
            if url not in self.old_urls:
                self.log.debug('Download m3u8 ts: %s', url)
                name_index += 1
                clip_file = pjoin(tmp_path, '%02d_%s.tmp' % (name_index, hash(url)))
                clips.append((clip_file, url))
                thread = M3u8.__DownloadThread(url, filename=clip_file, log=self.log)
                self.mgr.addThreads([thread])
                count += 1
        try:
            self.mgr.startAll()
            self.mgr.joinAll()

            for clip_file, clip_url in clips:
                if not os.path.exists(clip_file):
                    self.log.warn('clip file not exists: %s', clip_file)
                    continue
                self.log.debug('==> write: %s', clip_file)
                with open(clip_file, 'rb') as fp:
                    output_fp.write(fp.read())
                os.remove(clip_file)
                self.old_urls[clip_url] = True
        except:
            self.mgr.stopAll()
            self.mgr.joinAll()
            for clip_file, clip_url in clips:
                if os.path.exists(clip_file):
                    os.remove(clip_file)
            raise
        return count, len(urls), targetduration

    class __DownloadThread(ThreadBase):

        def __init__(self, url, filename, log):
            ThreadBase.__init__(self, log=log)
            self.url = url
            self.filename = filename
            self.miniaxel = MiniAxel()

        def stop(self):
            ThreadBase.stop(self)
            self.miniaxel.terminate_dl()

        def run(self):
            self.miniaxel.dl(self.url, out=self.filename, n=3)
            self.log.debug('--> dl ok: %s', self.filename)


class ClipDownloader(ThreadBase):

    def __init__(self, url, fp, duration=None):
        ThreadBase.__init__(self)
        self.url = url
        self.fp = fp
        self.dl_handler = None

    def terminate_dl(self):
        ThreadBase.stop(self)
        if self.dl_handler:
            self.dl_handler.stop_dl()
            self.dl_handler.wait_stop()

    def run(self):
        try:
            self.dl_handler = HttpDownloadClipHandler(fp=self.fp)
        except:
            if self.dl_handler:
                self.dl_handler.stop_dl()
                self.dl_handler.wait_stop()
            raise


class DownloadLiveStream:

    def __init__(self, log):
        self.log = log

    def recode(self, url, out_dir, duration=None, proxy=None):
        assert duration is None or duration > 0
        url = url.strip(' \n')
        url_base = filter_host(url)
        http = HttpUtil(timeout=10)
        if proxy:
            http.set_proxy({'http': proxy})
        self.log.info("|=> begin: %s", url)
        if duration:
            self.log.info("|duration: %s", duration)
        util.assure_path(out_dir)
        outfile = pjoin(out_dir, util.get_time_string() + ".ts")
        self.log.info("|=> output: %s", outfile)
        start_at = time.time()
        with open(outfile, 'wb') as fp:
            self.__recode(url, url_base=url_base, fp=fp, duration=duration, http=http)
        self.log.info("|=> end: total=%.2fs, out=%s", time.time() - start_at, outfile)

    def __recode(self, url, url_base, fp, duration, http):
        start_at = time.time()
        stop_at = 0
        if duration:
            stop_at = start_at + duration
        m3u8 =  None
        dl_handler = None
        while True:
            if duration and time.time() >= stop_at:
                if dl_handler:
                    dl_handler.terminate_dl()
                if m3u8:
                    m3u8.terminate_dl(3)
                break
            try:
                if url.find('m3u8') > 0 or self.__is_url_file(url):
                    self.log.debug('dl_stream=>m3u8: %s', url)
                    m3u8 = M3u8(http, log=self.log)
                    m3u8.dl_stream(url, url_base, fp)
                    return
                else:
                    self.log.debug('dl_stream=>single ts file: %s', url)
                    dl_handler = ClipDownloader(url, fp)
                    http.fetch(url, dl_handler)
                    return
            except urllib2.URLError as e:
                self.log.exception(e)
                self.log.warn('===> offline, retry in one seconds')
                time.sleep(1)
            except:
                if dl_handler:
                    dl_handler.terminate_dl()
                if m3u8:
                    m3u8.terminate_dl(3)
                raise

    def __is_url_file(self, url):
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
    DownloadLiveStream().recode(sub_addr[channel_list[channel_id]], duration, out_dir)


def parse_args(config):
    usage = """./dllive [-i|l][-c config][-o out_put_path][-f favorite][-d duration]"""
    import argparse
    parser=argparse.ArgumentParser(usage=usage, description='download live stream', version='0.1')
    parser.add_argument('-c', '--config', default='config.ini')
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
    if args.config != 'config.ini':
        config = Config(config=args.config)
        args = parse_args(config)
    log = util.get_logger(logfile=config.log, level=config.log_level)
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
        script_path = util.script_path(__file__)
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
    dls.recode(url=live_url, out_dir=args.out_dir, duration=args.duration, proxy=proxy)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
