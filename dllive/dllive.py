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
        self.live_url = cfg.get('default', 'live_url')
        self.pythonpath = cfg.get('environment', 'pythonpath')
        self.address_file = cfg.get('address_file', 'name')
        self.proxy_addr = cfg.get('proxy', 'addr')
        self.proxy_enable = cfg.getboolean('proxy', 'enable')
        self.favorites = cfg.items('favorites')
config = Config()

sys.path.insert(0, config.pythonpath)
from vavava.httputil import HttpUtil
from vavava.httputil import DownloadStreamHandler
from vavava import util
util.set_default_utf8()
LOG = util.get_logger()
CHARSET = "utf-8"

def filter_host(url):
    if url.find('ifeng.com') > 0:
        return re.match('(^http[s]?://[^/?]*/)', url).group(0)
    else:
        return re.match('(^http[s]?://.*/)', url).group(0)

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

class DownloadLiveStream:
    def _init(self, live_url, duration, output):
        self.url = live_url
        self.url_base = filter_host(self.url)
        self.duration = duration
        self.odir = output
        self.start = util.get_time_string()
        self.filter = dict()
        self.http = HttpUtil(charset="utf-8")
        self.http.add_header('Referer', self.url_base)
        if config.proxy_enable:
            self.http.set_proxy({'http': config.proxy_addr})

    def get_m3u8_list(self, url, url_base):
        results = []
        m3u8 = self.http.get(url)
        urls = m3u8.splitlines(False)
        for url in urls:
            if not url.startswith('#'):
                print '===?', url
                url = urllib.basejoin(url_base, url)
                if url.endswith('.m3u8'):
                    return self.get_m3u8_list(url, url_base)
                results.append(url)
        return results

    def _dl_m3u8(self, url, duration, ofp):
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
            count = self._dl_m3u81(url, duration, ofp)
            wait = (abs(count)-1)*12 - (time.time() - t1)
            print 'sleep==>', wait
            if wait > 5:
                sleep(wait)

    def _dl_m3u81(self, url, duration, ofp):
        urls = self.get_m3u8_list(url, self.url_base)
        count = 0
        for url in urls:
            if not self.filter.has_key(url):
                print 'Download: ', url
                download_handle = DownloadStreamHandler(ofp, duration)
                self.http.fetch(url, download_handle)
                self.filter[url] = ''
                count += 1
        return count

    def _dl_ts(self, url, duration, ofp):
        print 'Download: ', url
        download_handle = DownloadStreamHandler(ofp, duration)
        self.http.fetch(url, download_handle)

    def _is_url_file(self, url):
        import urllib2
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        info = resp.info()
        if info.type.find('url') > 0:
            return True
        return False

    def recode(self, url, duration, output):
        self._init(url, duration, output)
        LOG.info("[start.... ] %s", util.get_time_string())
        try:
            outfile = pjoin(self.odir, util.get_time_string() + ".flv")
            ofp = open(outfile, 'w')
            if url.endswith('.m3u8') or self._is_url_file(url):
                self._dl_m3u8(url, duration, ofp)
            else:
                self._dl_ts(url, duration, ofp)
            LOG.info("[stop] %s", util.get_time_string())
        except Exception as e:
            LOG.exception(e)
        finally:
            pass

def main():
    import getopt
    import sys
    channel = None
    duration = 0
    path = os.path.join(os.environ['HOME'], 'Downloads')
    opts, args = getopt.getopt(sys.argv[1:], "d:f:p:j:l")
    for k, v in opts:
        if k in ("-d"):
            duration = float(v)
        elif k in ("-p"):
            path = os.path.abspath(v)
        elif k in ("-f"):
            for f in config.favorites:
                if f[0] == v:
                    channel = f[1]
            if channel is None:
                raise 'asdfadfas'
        elif k in ("-l"):
            script_path = util.get_file_path(__file__)
            os.system('python %s/xbmc_5ivdo.py -t 直播 > %s/%s'%(
                script_path, script_path, config.address_file))
            exit(0)
    if channel:
        pass
    elif len(args) > 0:
        channel = get_channel_url(args[0])[0]
    else:
        channel = config.live_url
    LOG.info('>>>>>>>>>>>>>>> %s >>>>>>>>>>>>>>>', channel)
    LOG.info('>>>>>>>>>>>>>>> %s ', path)
    LOG.info('>>>>>>>>>>>>>>> %s ', duration)
    DownloadLiveStream().recode(channel, duration, path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'end by user'
        exit(0)
