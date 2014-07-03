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

import re
from vavava import httputil

def escape_file_path(path):
    path = path.replace('/', '_')
    path = path.replace('\\', '_')
    path = path.replace('*', '_')
    path = path.replace('?', '_')
    path = path.replace('\'', '_')
    return path

class PlayListFilterBase:
    def handle(self, url):
        pass

class YoukuFilter(PlayListFilterBase):
    def parse_playlist_pages(self, url):
        html = httputil.HttpUtil().get(url)
        reg = """<span class="l_img"[^>]*location='(?P<asd>[^>]*?)';return false;">"""
        return self.parse_playlist_title(html), re.findall(reg, html, flags=re.S)

    def parse_playlist_title(self, html):
        reg = r'<h1 class="title" title="(?P<as>[^>]*?)">'
        return escape_file_path(re.findall(reg, html, flags=re.S)[0])

    def handle(self, url):
        if url.find('youku.com') > 0:
            return self.parse_playlist_pages(url)


def main():
    url = r'http://v.youku.com/v_show/id_XNjcxNjQ4ODcy.html?f=21871965'
    urls, title = YoukuFilter().handle(url)
    print title
    print urls


if __name__ == "__main__":
    # signal_handler = util.SignalHandlerBase()
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        raise
    finally:
        pass


