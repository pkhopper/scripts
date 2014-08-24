#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
from vavava import httputil

default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
exists = os.path.exists


def to_native_string(s):
    if type(s) == unicode:
        return s.encode(default_encoding)
    else:
        return s


def escape_file_path(path):
    path = path.replace('/', '_')
    path = path.replace('\\', '_')
    path = path.replace('*', '_')
    path = path.replace('?', '_')
    path = path.replace('\'', '_')
    return path


def guess_ext(urls, title):
    for url in urls:
        if url.find('mp4') >= 0:
            return 'mp4'
    if title.find('mp4') >= 0:
        return 'mp4'
    return 'flv'


class Wget:

    def __init__(self):
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) ' \
                         r'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' \
                         r'33.0.1750.149 Safari/537.36'

    def get(self, url, out=None, headers=None, proxy=None):
        cmd = "wget -c --user-agent='%s'" % (self.useragent)
        if headers:
            for k, v in headers.items():
                if k in ('referer'):
                    cmd += " --referer='%s'" % (v)
                else:
                    cmd += " --header='%s:%s'" % (k, v)
        if out:
            cmd += " --output-document='%s'" % (out)
        if not proxy:
            cmd += " --no-proxy"
        cmd += " '%s'" % (url)
        self.__exec(cmd)

    def __exec(self, cmd):
        print cmd
        self.result = os.system(cmd)
        if self.result != 0:
            raise StandardError("result=%d  %s" % (self.result, cmd))


class Axel:
    def __init__(self):
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) ' \
                         r'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 ' \
                         r'Safari/537.36'

    def get(self, url, out=None, n=None, headers=None):
        cmd = "axel -v -a -U '%s'" % (self.useragent)
        if headers:
            for k, v in headers.items():
                cmd += " -H '%s:%s'" % (k, v)
        if n:
            cmd += " -n %d" % (n)
        if out:
            cmd += " -o '%s'" % (out)
        cmd += " '%s'" % (url)
        self.__exec(cmd)

    def __exec(self, cmd):
        print cmd
        self.result = os.system(cmd)
        if self.result != 0:
            raise StandardError("result=%d  %s" % (self.result, cmd))
