#!/usr/bin/env python
# coding=utf-8

import os
import sys
import json
from vavava import util
util.set_default_utf8()

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath

user_path = os.environ['HOME']

def dump_path(path):
    return path.replace(r"%(home)s", user_path)

def dl_u2b(url, config):
    config  = config['u2b']
    cmd = dump_path(config['cmd'])
    out_dir = dump_path(config['out_dir'])
    proxy = config['proxy']
    cache = config['cache']
    cmd += r' --proxy "%s"' % proxy
    cmd += r' --o "%s"' % out_dir
    cmd += r' --cache-dir "%s"' % cache
    cmd += r' "%s"' % url
    os.system(cmd)

def dl_other(url, config):
    config  = config['xiazai']
    cmd = dump_path(config['cmd'])
    out_dir = dump_path(config['out_dir'])
    os.chdir(out_dir)
    cmd += r' "%s"' % url
    os.system(cmd)

def dl_urls(m3ufile, config):
    default_out = dump_path(config['default']['out_dir'])
    out_dir = dump_path(config['downloads']['out_dir'])
    lib_dir = dump_path(config['downloads']['lib_dir'])
    os.chdir(out_dir)
    if not m3ufile:
        m3us = []
        for m3u in os.listdir('.'):
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
    sys.path.insert(0, lib_dir)
    dlvideo = __import__('dlvideo')
    dlvideo.downloads(m3ufile, out_dir)

def main():
    if os.path.islink(__file__):
        curr_dir = dirname(abspath(os.readlink(__file__)))
    else:
        curr_dir = dirname(abspath(__file__))
    config = json.load(open(pjoin(curr_dir, 'dlvideo.json')))
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    if not url or not url.startswith("http"):
        dl_urls(url, config)
    elif url.find("youtube.com") >= 0:
        dl_u2b(url, config)
    else:
        dl_other(url, config)
    os.system(r'say "download finished!!"')


if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
    except Exception, e:
        raise
    finally:
        pass


