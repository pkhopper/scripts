#!/usr/bin/env python
# coding=utf-8

import os
import sys
import time
import urllib
import re
from time import sleep

dirname = os.path.dirname
abspath = os.path.abspath
pjoin = os.path.join
user_path = os.environ['HOME']

class Config:
    def __init__(self, config='config.ini'):
        dump_path = lambda path: path.replace(r"%(home)s", user_path)
        if os.path.islink(__file__):
            script_path = dirname(abspath(os.readlink(__file__)))
        else:
            script_path = dirname(abspath(__file__))
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.read(pjoin(script_path, config))
        self.out_dir = cfg.get('default', 'out_dir')
        self.channel = cfg.get('default', 'channel')
        self.duration = cfg.getint('default', 'duration')
        self.log_file = cfg.get('default', 'log_file')
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
config = Config()

sys.path.insert(0, config.pythonpath)
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util
util.set_default_utf8()
LOG = util.get_logger(config.log_file, config.log_level)
CHARSET = "utf-8"

def get_channel_url(name):
    urls = []
    channels = open(config.address_file, 'r').readlines()
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
        LOG.debug('ifeng.com filter: %s', url)
        return re.match('(^http[s]?://[^/?]*/)', url).group(0)
    else:
        return re.match('(^http[s]?://.*/)', url).group(0)

class M3u8:
    def __init__(self, http):
        self.http = http
        self.old_ts_filter = dict()

    def _get_index(self, url, url_base=None):
        results = []
        TARGETDURATION = 2
        if url_base is None:
            url_base = re.match('(^http[s]?://.*/)', url).group(0)
        m3u8 = self.http.get(url)
        urls = m3u8.splitlines(False)
        for url in urls:
            if not url.startswith('#'):
                LOG.debug('[m3u8_iner_url] %s', url)
                url = urllib.basejoin(url_base, url)
                if url.endswith('.m3u8'):
                    return self._get_index(url, url_base)
                results.append(url)
            elif url.lower().find('targetduration') > 0:
                TARGETDURATION = int(url.split(':')[1])
                LOG.debug('TARGETDURATION=%s', TARGETDURATION)
        return results, TARGETDURATION

    def _dl_1(self, url, url_base, duration, ofp):
        urls, TARGETDURATION = self._get_index(url, url_base)
        count = 0
        for url in urls:
            if not self.old_ts_filter.has_key(url):
                LOG.debug('Download m3u8 ts: %s', url)
                download_handle = DownloadStreamHandler(ofp, duration)
                self.http.fetch(url, download_handle)
                self.old_ts_filter[url] = ''
                count += 1
        return count, TARGETDURATION

    def dl(self, url, url_base, duration, ofp):
        start = time.time()
        stop = 0
        if duration > 0:
            stop = duration + start
        while True:
            curr = time.time()
            tt = stop - curr
            if duration > 0 and tt < 0:
                break
            t1 = time.time()
            count, TARGETDURATION = self._dl_1(url, url_base, duration, ofp)
            wait = (count-1)*TARGETDURATION - (time.time() - t1)
            LOG.debug('sleep==> %s', wait)
            if wait > 0:
                sleep(wait)

class DownloadLiveStream:

    def _init(self, live_url, duration, out_dir):
        self.url = live_url.strip(' \n')
        self.url_base = filter_host(self.url)
        self.duration = duration
        self.odir = out_dir
        self.start = time.time()
        self.http = HttpUtil(charset="utf-8", timeout=10)
        self.http.add_header('Referer', self.url_base)
        if config.proxy_enable:
            self.http.set_proxy({'http': config.proxy_addr})
        self.m3u8 = M3u8(self.http)

    def _dl_ts(self, url, duration, ofp):
        LOG.debug('dl ts: %s', url)
        download_handle = DownloadStreamHandler(ofp, duration)
        self.http.fetch(url, download_handle)

    def _is_url_file(self, url):
        import urllib2
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        info = resp.info()
        return info.type.find('url') > 0

    def _recode(self, url, duration, ofp):
        if url.endswith('.m3u8') or self._is_url_file(url):
            self.m3u8.dl(url, self.url_base, duration, ofp)
        else:
            self._dl_ts(url, duration, ofp)

    def recode(self, url, duration, output):
        self._init(url, duration, output)
        LOG.info("===>start: %s", util.get_time_string())
        LOG.info("===>url: %s", url)
        LOG.info("===>duration: %d", duration)
        self.outfile = pjoin(self.odir, util.get_time_string() + ".ts")
        LOG.info("===>output: %s", self.outfile)
        ofp = open(self.outfile, 'w')
        try:
            self._recode(self.url, duration, ofp)
            LOG.info("===>stopped %s", util.get_time_string())
        except KeyboardInterrupt as e:
            LOG.info('===>stopped by user: %s', self.outfile)
            raise e
        except Exception as e:
            LOG.exception(e)
            new_duration = time.time() - self.start - duration
            if new_duration == 0:
                LOG.info("===>stopped, but exception happened. %s", util.get_time_string())
                exit(0)
            if duration == 0:
                new_duration = 0
            if new_duration >= 0:
                LOG.info('===>exception happened, restart ...')
                self._recode(url, duration, ofp)

def interact():
    LOG.info('===>interact mode')
    channel = raw_input('channel?')
    address = open(config.address_file, 'r').readlines()
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
    DownloadLiveStream().recode(sub_addr[channel_list[channel_id]], config.duration, config.out_dir)

def useage():
    print """\
    dllive -d duration
    dllive -f favorites
    dllive -o output_path
    dllive -l
    """

def main():
    import getopt
    import sys
    channel = None
    duration = 0
    path = os.path.join(os.environ['HOME'], 'Downloads')
    opts, args = getopt.getopt(sys.argv[1:], "d:f:o:lhi")
    for k, v in opts:
        if k in ("-d"):
            duration = float(v)
        elif k in ("-h"):
            useage()
            exit(0)
        elif k in ("-i"):
            interact()
            exit(0)
        elif k in ("-o"):
            path = os.path.abspath(v)
        elif k in ("-f"):
            for f in config.favorites:
                if f[0] == v:
                    channel = f[1]
            if channel is None:
                raise 'asdfadfas'
        elif k in ("-l"):
            script_path = util.get_file_path(__file__)
            os.system('python %s/xbmc_5ivdo.py -t 直播 > %s'%(
                script_path, config.address_file)
            )
            exit(0)
    if channel:
        pass
    elif len(args) > 0:
        channel = get_channel_url(args[0])[0]
    else:
        channel = config.live_url
    LOG.debug('>>>>>>>>>>>>>>> %s >>>>>>>>>>>>>>>', channel)
    LOG.debug('>>>>>>>>>>>>>>> %s ', path)
    LOG.debug('>>>>>>>>>>>>>>> %s ', duration)
    DownloadLiveStream().recode(channel, duration, path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)

