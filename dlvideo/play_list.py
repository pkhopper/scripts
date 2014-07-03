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

class PlayListFilterBase:
    def handle(self, url):
        pass

class YoukuFilter(PlayListFilterBase):
    def parse_playlist_pages(self, url):
        html = httputil.HttpUtil().get(url)
        reg = """<span class="l_img"[^>]*location='(?P<asd>[^>]*?)';return false;">"""
        return re.findall(reg, html, flags=re.S)
    def handle(self, url):
        if url.find('youku.com') > 0:
            return self.parse_playlist_pages(url)


def main():
    pass


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


