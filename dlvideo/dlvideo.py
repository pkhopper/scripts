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
        self.out_dir = cfg.get('default', 'out_dir')
        self.format = cfg.get('default', 'format')
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

# sys.path.insert(0, config.lib_dir)
# common = __import__('common')
# download_urls = common.download_urls
import dl_helper
download_urls = dl_helper.download_urls


def dl_u2b(url, argv):
    cmd = config.u2b_cmd
    cmd += r' --proxy "%s"' % config.u2b_proxy
    cmd += r' --o "%s"' % config.u2b_title_format
    cmd += r' --cache-dir "%s"' % config.u2b_cache
    for arg in argv:
        cmd += ' ' + arg
    cmd += r' %s' % url
    print '==>', cmd
    os.system(cmd)

def dl_youkulixian(url):
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

def dl_flvcd(url):
    import urllib
    from re import findall
    from vavava.httputil import HttpUtil
    parse_url = 'http://www.flvcd.com/parse.php?'
    parse_url += 'kw='+ urllib.quote(url)
    parse_url += '&flag=one'
    if config.format == 'super':
        parse_url += '&format=super'
    http = HttpUtil()
    http.add_header('Referer', parse_url)
    html = http.get(parse_url).decode('gb2312')
    try:
        m3u = findall(r'name="inf" value="(?P<as>[^"]*)"', html)[0]
        title = findall(u'<strong>当前解析视频：</strong>(?P<as>[^<]*)<strong>', html)[0]
    except:
        print 'not support'
        os.system('say "not support."')
        return
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
    result = download_urls(urllist, title, ext, odir=config.out_dir,
                  nthread=10, nperfile=True, refer=refer, merge=True)
    return result

def dl_dispatch(url, is_m3u=False):
    if is_m3u:
        dl_m3u(url)
        return
    if url.find("youtube.com") >= 0:
        dl_u2b(url, sys.argv[2:])
    elif config.flvcd['default']:
        import re
        available_4flvcd = \
            lambda x: re.findall(r'(?P<as>[^\\/\.]*\.[^\\/\.]*)[\\|/]', x.lower())[0]
        site = available_4flvcd(url)
        if site not in config.flvcd or config.flvcd[site]:
            dl_flvcd(url)
        else:
            dl_youkulixian(url)

def useage():
    print """\
    dllive -f super|normal
    dllive -o output_path
    """

def main():
    import getopt
    is_m3u = False
    opts, args = getopt.getopt(sys.argv[1:], "f:o:hm")
    for k, v in opts:
        if k in ("-f"):
            config.format = v
        elif k in ("-m"):
            is_m3u = True
        elif k in ("-o"):
            config.out_dir = v
        elif k in ("-h"):
            useage()
            exit(0)
    urls = args
    for url in urls:
        dl_dispatch(url, is_m3u)

if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
        os.system(r'say "download finished!!"')
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception, e:
        os.system(r'say "download failed!!"')
        raise
    finally:
        pass


