#!/usr/bin/env python
# coding=utf-8

import os
import time
import urllib
import urllib2
import re
import threading
from time import sleep

from vavava.vavava.httputil import HttpUtil
from vavava.vavava.httputil import MiniAxel
from vavava.vavava.httputil import DownloadStreamHandler
from vavava import util


util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

class Config:
    def __init__(self, config=None):
        if os.path.islink(__file__):
            script_dir = pdirname(pabspath(os.readlink(__file__)))
        else:
            script_dir = pdirname(pabspath(__file__))
        config_file = config
        if config_file:
            config_file = pabspath(config_file)
        else:
            config_file = pjoin(script_dir, "config.ini")
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.read(config_file)
        self.out_dir = cfg.get('default', 'out_dir')
        self.channel = cfg.get('default', 'channel')
        self.duration = cfg.getint('default', 'duration')
        self.log = cfg.get('default', 'log')
        self.log_level = cfg.get('default', 'log_level')
        self.live_url = cfg.get('default', 'live_url')
        self.pythonpath = cfg.get('environment', 'pythonpath')
        self.address_file = cfg.get('address_file', 'name')
        self.proxy_addr = cfg.get('proxy', 'addr')
        self.proxy_enable = cfg.getboolean('proxy', 'enable')
        self.favorites = cfg.items('favorites')
        lvlconvert = {
            'critical' : 50,
            'fatal' : 50,
            'error' : 40,
            'warning' : 30,
            'warn' : 30,
            'info' : 20,
            'debug' : 10,
            'notset' : 0
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
        log.debug('ifeng.com filter: %s', url)
        return re.match('(^http[s]?://[^/?]*/)', url).group(0)
    else:
        return re.match('(^http[s]?://.*/)', url).group(0)

class M3u8:
    def __init__(self, http):
        self.http = http
        self.old_urls = dict()
        self.threads = None

    def get_curr_index(self, url, url_base=None):
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
                log.debug('m3u8InerUrl ==> %s', url)
                if not url.startswith('http'):
                    url = urllib.basejoin(url_base, url)
                if url.endswith('.m3u8'):
                    return self.get_curr_index(url, url_base)
                lines.append(url)
            elif url.lower().find('targetduration') > 0:
                targetduration = int(url.split(':')[1])
                log.debug('targetduration=%d', targetduration)
        return lines, targetduration

    def get_curr_stream(self, url, url_base, duration, ofp):
        urls, targetduration = self.get_curr_index(url, url_base)
        # count = self.__dl_single(urls, ofp=ofp, duration=duration)
        count = self.__dl_multiple(urls, ofp=ofp, duration=duration)
        return count, len(urls), targetduration

    def __dl_single(self, urls, ofp, duration):
        count = 0
        for url in urls:
            if not self.old_urls.has_key(url):
                log.debug('Download m3u8 ts: %s', url)
                download_handle = DownloadStreamHandler(ofp, duration)
                self.http.fetch(url, download_handle)
                self.old_urls[url] = ''
                count += 1
        return count

    def __dl_multiple(self, urls, ofp, duration):
        self.threads = []
        name_index = 0
        count = 0
        tmp_files = []
        util.assure_path(pjoin(config.out_dir, '.dllive'))
        for url in urls:
            if not self.old_urls.has_key(url):
                log.debug('Download m3u8 ts: %s', url)
                name_index += 1
                tmp_file = '{}.{}.tmp'.format(name_index, hash(url))
                tmp_file = pjoin(config.out_dir, '.dllive', tmp_file)
                tmp_files.append((tmp_file, url))
                self.threads.append(M3u8.DownloadThread(url, filename=tmp_file, duration=duration))
                count += 1
        for i, th in enumerate(self.threads):
            th.join()
            if not th.finish:
                log.error('thread exit with unfinished work.[%d]'%i)
                break
            log.debug('==> write file: %s', tmp_files[i][0])
            with open(tmp_files[i][0], 'r') as fp:
                ofp.write(fp.read())
            os.remove(tmp_files[i][0])
            self.old_urls[tmp_files[i][1]] = ''
        return count

    def dl_stream(self, url, url_base, duration, ofp):
        start_time = time.time()
        total_server = 0
        stop_time = duration + start_time
        while True:
            before = time.time()
            count, total, targetduration = self.get_curr_stream(url, url_base, duration, ofp)
            after = time.time()
            curr_local = after - before   # time_transfer
            curr_server = count * targetduration
            curr_buffered = curr_server - curr_local
            total_server += curr_server
            total_local = after - start_time
            total_buffered = total_server - total_local
            # T=total;C=current;
            log.debug('CURR:%.2f/%.2f(%.2f);TOTAL:%.2f/%.2f(%.2f);DURATION:%d;COUNT:%d',
                      curr_local, curr_server, curr_buffered,
                      total_local, total_server, total_buffered,
                      targetduration, count)
            if duration > 0 and stop_time - after < max(curr_buffered, 0.01):
                log.debug(r"===> time's up.")
                break
            if count == 0 \
                    or (curr_buffered > targetduration and total_buffered > targetduration):
                wait = min(10, targetduration)
                log.debug('sleep(%d)', wait)
                sleep(wait)

    class DownloadThread:
        def __init__(self, url, filename, duration=0):
            self.url = url
            self.filename = filename
            self.duration = duration
            self.thread = threading.Thread(target=self._run)
            self.finish = False
            self.join = self.thread.join
            self.thread.start()
        def _run(self,*_args, **_kwargs):
            with open(self.filename, 'w') as fp:
                # # 1.
                # download_handle = DownloadStreamHandler(fp, self.duration)
                # HttpUtil().fetch(self.url, download_handle)
                # 2.
                MiniAxel().dl(self.url, fp=fp, n=3)
                self.finish = True
            log.debug('--> file download ok: %s', self.filename)


class DownloadLiveStream:

    def __prepare(self, live_url, duration, out_dir, proxy=None):
        self.url = live_url.strip(' \n')
        self.url_base = filter_host(self.url)
        self.duration = duration
        self.none_stop = duration == 0
        self.odir = out_dir
        self.http = HttpUtil(charset="utf-8", timeout=10)
        if proxy:
            self.http.set_proxy({'http': proxy})
        self.m3u8 = M3u8(self.http)

    def __is_url_file(self, url):
        import urllib2
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        info = resp.info()
        return info.type.find('url') > 0

    def __recode(self, url, duration, ofp):
        self.start = time.time()
        self.stop = self.start + duration
        while duration == 0 or time.time() < self.stop:
            try:
                if url.find('m3u8') > 0 or self.__is_url_file(url):
                    log.debug('dl_stream m3u8: %s', url)
                    return self.m3u8.dl_stream(url, self.url_base, duration, ofp)
                else:
                    log.debug('dl_stream ts: %s', url)
                    self.http.fetch(url, DownloadStreamHandler(ofp, duration))
            except KeyboardInterrupt as e:
                raise e
            except urllib2.URLError as e:
                log.exception(e)
                log.error('===> offline, retry in 2 seconds. <===')
                time.sleep(2)
            except Exception as e:
                log.exception(e)

    def recode(self, url, output, duration=0, proxy=None):
        self.__prepare(url, duration, output, proxy)
        log.info("====>start: duration=%.2f, url=%s", duration, url)
        util.assure_path(self.odir)
        self.outfile = pjoin(self.odir, util.get_time_string() + ".ts")
        log.info("===> output: %s", self.outfile)
        with open(self.outfile, 'a+') as ofp:
            self.__recode(self.url, duration=duration, ofp=ofp)
        log.info("====>stopped (total=%.2fs,duration=%.2fs, out=%s)",
                 time.time() - self.start, duration, self.outfile)

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
    parser.add_argument('-d', '--duration', type=float, default=config.duration)
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
        script_path = util.get_file_path(__file__)
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

    DownloadLiveStream().recode(url=live_url, output=args.out_dir,
                                duration=args.duration, proxy=proxy)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
