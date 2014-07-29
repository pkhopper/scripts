#!/usr/bin/env python
# coding=utf-8

import os
import sys
import dl_helper
from vavava import util
from config import Config as _Config


util.set_default_utf8()
import parsers

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
user_path = os.environ['HOME']

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

def dispatch(url):
    if url.find("youtube.com") >= 0:
        dl_u2b(url, sys.argv[2:])
    else:
        parser = parsers.getVidPageParser(url)
        urls, title, ext, nperfile, headers = parser.info(url, vidfmt=config.format)
        if nperfile != 1:
            nperfile = config.nperfile
        downloader = dl_helper.Downloader(nperfile=nperfile, nthread=config.nthread, log=log)
        downloader.download(urls, title=title, out_dir=config.out_dir, ext=ext, headers=headers)

def parse_args(config):
    import argparse
    usage = """./dlvideo [-m][-l][-c config][-o output][-f format] url ..."""
    parser=argparse.ArgumentParser(usage=usage, description='download net video', version='0.1')
    parser.add_argument('urls', nargs='*', help='urls')
    # parser.add_argument('urls', nargs='+', help='urls')
    parser.add_argument('-c', '--config', default='config.ini')
    parser.add_argument('-o', '--odir')
    parser.add_argument('-i', '--interact', action='store_true')
    parser.add_argument('-l', '--play-list', dest='play_list', action='store_true')
    parser.add_argument('-f', '--format', help='video format:super, normal',choices=['0', '1', '2', '3'])
    args = parser.parse_args()
    # print args
    return args

def init_args_config():
    config = _Config()
    args = parse_args(config=config)
    if args.config != 'config.ini':
        config = _Config(config=args.config)
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
        util.assure_path(config.out_dir)
        with open(pjoin(config.out_dir, 'url.txt'), 'w') as fp:
            fp.writelines([url + "\n\n"])
            for i, clip in enumerate(args.urls):
                fp.writelines(["[%03d] %s\n"%(i, clip)])
    if args.interact:
        import interface
        args.urls = interface.UserInterface(config.out_dir).console()

    for i, url in enumerate(args.urls):
        try:
            log.info('[==START==][%03d/%03d] %s', i, len(args.urls), url)
            dispatch(url)
            log.info('[==END==][%03d/%03d] %s', i, len(args.urls), url)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            log.error('==> exception happened: %s', url)
            log.exception(e)

if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
        if util.check_cmd('say'):
            os.system(r'say "download finished!!"')
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        if util.check_cmd('say'):
            os.system(r'say "download failed!!"')
        raise


