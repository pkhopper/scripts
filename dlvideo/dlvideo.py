#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
import dl_helper
util.set_default_utf8()
import parsers

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
user_path = os.environ['HOME']

class Config:
    def __init__(self, config=None):
        script_dir = util.get_file_path(__file__)
        config_file = config
        if config_file:
            config_file = pabspath(config_file)
        else:
            config_file = pjoin(script_dir, 'config.ini')
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.read(config_file)
        self.out_dir = cfg.get('default', 'out_dir')
        self.format = cfg.getint('default', 'format')
        self.nthread = cfg.getint('network', 'nthread')
        self.nperfile = cfg.getint('network', 'nperfile')
        self.log = cfg.get('default', 'log')
        self.log_level = cfg.get('default', 'log_level')
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

def dl_u2b(url, argv):
    cmd = config.u2b_cmd
    cmd += r' --proxy "%s"' % config.u2b_proxy
    cmd += r' --o "%s"' % config.u2b_title_format
    cmd += r' --cache-dir "%s"' % config.u2b_cache
    for arg in argv:
        cmd += ' ' + arg
    cmd += r' %s' % url
    log.debug('==> %s', cmd)
    os.system(cmd)

def dl_flvcd(url):
    from urllib import quote
    from re import findall
    from vavava.httputil import HttpUtil
    parse_url = 'http://www.flvcd.com/parse.php?'
    parse_url += 'kw='+ quote(url)
    parse_url += '&flag=one'
    format = ['', 'high', 'super', 'real']
    if config.format > 0:
        parse_url += '&format=%s'%format[config.format]
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
    downloader = dl_helper.Downloader(
        nperfile=config.nperfile, nthread=config.nthread, log=log)
    urls = [url for url in m3u.split('|')]
    downloader.download(urls, title=title, out_dir=config.out_dir)
    return title

def dl_dispatch(url):
    local_file = None
    if url.find("youtube.com") >= 0:
        dl_u2b(url, sys.argv[2:])
    elif config.flvcd['default']:
        import re
        available_4flvcd = \
            lambda x: re.findall(r'(?P<as>[^\\/\.]*\.[^\\/\.]*)[\\|/]', x.lower())[0]
        site = available_4flvcd(url)
        if site not in config.flvcd or config.flvcd[site]:
            local_file = dl_flvcd(url)
        else:
            urls, title, ext, nperfile, referer = \
                parsers.getVidPageParser(url).info(url, vidfmt=config.format)
            downloader = dl_helper.Downloader(
                nperfile=config.nperfile, nthread=config.nthread, log=log)
            if nperfile == 1:
                downloader.nperfile = 1
            downloader.download(
                urls, title=title, out_dir=config.out_dir, ext=ext, referer=referer)
        # log.info(r"[O.F.] %s" % local_file)

def parse_args(config):
    import argparse
    usage = """./dlvideo [-m][-l][-c config][-o output][-f format] url ..."""
    parser=argparse.ArgumentParser(usage=usage, description='download net video', version='0.1')
    parser.add_argument('urls', nargs='+', help='urls')
    parser.add_argument('-c', '--config', default='config.ini')
    parser.add_argument('-o', '--odir')
    parser.add_argument('--play-list', '-l', dest='play_list', action='store_true')
    parser.add_argument('-f', '--format', help='video format:super, normal',choices=['0', '1', '2', '3'])
    args = parser.parse_args()
    # print args
    return args

def init_args_config():
    config = Config()
    args = parse_args(config=config)
    if args.config != 'config.ini':
        config = Config(config=args.config)
        args = parse_args(config=config)
    log = util.get_logger(logfile=config.log, level=config.log_level)
    return args, config, log

def main():
    global log
    global config
    args, config, log = init_args_config()
    dl_helper.log = log
    log.info('{}'.format(args))
    if args.odir:
        config.out_dir = args.odir
    if args.format:
        config.format = int(args.format)
    if args.play_list:
        url = args.urls[0]
        out_dir, args.urls = parsers.getPlayListParser(url).info(url)
        config.out_dir = pjoin(config.out_dir, out_dir)
        # util.assure_path(config.out_dir)
    for url in args.urls:
        try:
            log.info('[START] %s', url)
            dl_dispatch(url)
            log.info('[END] %s', url)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            log.error('==> exception happened: %s', url)
            log.exception(e)

if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
        os.system(r'say "download finished!!"')
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        os.system(r'say "download failed!!"')
        raise


