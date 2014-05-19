#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
util.set_default_utf8()

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']

class Config:
    def __init__(self, config='config.ini'):
        dump_path = lambda path: path.replace(r"%(home)s", user_path)
        if os.path.islink(__file__):
            curr_dir = dirname(abspath(os.readlink(__file__)))
        else:
            curr_dir = dirname(abspath(__file__))
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.read(pjoin(curr_dir, config))
        # self.flvcd = cfg.getboolean('default', 'flvcd')
        self.out_dir = cfg.get('default', 'out_dir')
        self.lib_dir = cfg.get('script', 'lib_dir')
        self.cmd = cfg.get('script', 'cmd')
        self.u2b_cmd = cfg.get('u2b', 'cmd')
        self.u2b_proxy = cfg.get('u2b', 'proxy')
        self.u2b_cache = cfg.get('u2b', 'cache')
        self.u2b_title_format = cfg.get('u2b', 'title_format', raw=True)
        self.u2b_create_dir = cfg.get('u2b', 'create_dir')
        self.flvcd = {}
        for k,v in cfg.items('flvcd'):
            self.flvcd[k] = v.lower() == 'true'
config = Config()

def dl_u2b(url):
    cmd = config.u2b_cmd
    cmd += r' --proxy "%s"' % config.u2b_proxy
    cmd += r' --o "%s"' % config.u2b_title_format
    cmd += r' --cache-dir "%s"' % config.u2b_cache
    cmd += r' "%s"' % url
    os.system(cmd)

def dl_other(url):
    cmd = config.cmd
    os.chdir(config.out_dir)
    cmd += r' "%s"' % url
    os.system(cmd)

def search_m3u(search_path):
    m3us = []
    for m3u in os.listdir(search_path):
        if m3u.endswith('.m3u') and os.path.isfile(m3u):
            m3us.append(m3u)
    if len(m3us) == 0:
        os.system('say m3u file not found!!')
        return
    elif len(m3us) == 1:
        m3ufile = m3us[0]
    else:
        i = 1
        for m3u in m3us:
            print "[%d] %s" % (i, m3u)
            i += 1
        pos = int(raw_input())
        m3ufile = m3us[pos-1]
    return pjoin(search_path, m3ufile)

def dl_m3u(m3ufile):
    import time
    out_dir = config.out_dir
    if not m3ufile:
        m3ufile = search_m3u(out_dir)
    urls = []
    for url in open(m3ufile, 'r').readlines():
        url = url.strip()
        if not url.startswith('#'):
            urls.append(url)
    if not urls[0].startswith("http:"):
        title = urls[0]
        urls = urls[1:]
    else:
        title = "%s-%s"%(time.strftime("%Y%m%d%H%M%S", time.localtime()), m3ufile)
    output_dir = pjoin(out_dir, title)
    if output_dir.endswith('.m3u'):
        output_dir = output_dir[:-4]
    if not os.path.isdir(output_dir):
        print output_dir
        os.mkdir(output_dir)
    dl_urls(urls, title)

def dl_from_flvcd(url):
    import urllib
    from re import findall
    from vavava.httputil import HttpUtil
    url1 = 'http://www.flvcd.com/parse.php?'
    url1 += 'kw='+ urllib.quote(url)
    url1 += '&flag=one'
    url1 += '&format=super'
    http = HttpUtil()
    http.add_header('Referer', url1)
    html = http.get(url1).decode('gb2312')
    m3u = findall(r'name="inf" value="(?P<as>[^"]*)"', html)[0]
    title = findall(u'<strong>当前解析视频：</strong>(?P<as>[^<]*)<strong>', html)[0]
    title = title.strip()

    dl_urls(urls=[url for url in m3u.split('|')], title=title, refer=url)

def dl_urls(urls, title, refer=None):
    urllist = []
    for url in urls:
        if url.startswith('http'):
            urllist.append(url)
    ext = 'flv'
    if urllist[0].find('mp4') > 0:
        ext = 'mp4'
    size = 1024*1024*100
    merge = True
    out_dir = config.out_dir
    lib_dir = config.lib_dir
    sys.path.insert(0, lib_dir)
    common = __import__('common')
    common.download_urls(urllist, title, ext, total_size=size,
                  output_dir=out_dir, refer=refer, merge=merge)

def available_4flvcd(url):
    import re
    result = re.findall(r'(?P<as>[^\\/\.]*\.[^\\/\.]*)[\\|/]', url.lower())[0]
    return result

def main():
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    if not url or not url.startswith("http"):
        dl_m3u(url)
    elif url.find("youtube.com") >= 0:
        dl_u2b(url)
    elif config.flvcd['default']:
        site = available_4flvcd(url)
        if site not in config.flvcd or config.flvcd[site]:
            dl_from_flvcd(url)
        else:
            dl_other(url)

if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
        os.system(r'say "download finished!!"')
    except Exception, e:
        os.system(r'say "download failed!!"')
        raise
    finally:
        pass


