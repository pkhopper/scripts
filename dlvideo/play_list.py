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
import BeautifulSoup

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
    def __items(self, html, soup):
        ul = soup.find('ul', attrs={'class': 'items'})
        lis = ul.findAll('li', attrs={'class': 'item'})
        return [li.a['href'] for li in lis]

    def __title(self, html, soup):
        h1 = soup.find("h1", attrs={'class': 'title'})
        title = h1.find('a').text
        subtitle = h1.find('span').text
        if title:
            return title
        else:
            return subtitle

    def handle(self, url):
        if url.find('youku.com') > 0:
            html = httputil.HttpUtil().get(url)
            soup = BeautifulSoup.BeautifulSoup(html)
            self.title = self.__title(html, soup)
            self.items = self.__items(html, soup)
            return self.title, self.items


def main():
    url = r'http://v.youku.com/v_show/id_XNjcxNjQ4ODcy.html?f=21871965'
    url = r'http://v.youku.com/v_show/id_XNTE2NjE2NzU2.html'
    title, urls = YoukuFilter().handle(url)
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


