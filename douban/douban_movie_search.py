#!/usr/bin/env python
# coding=utf-8

import sys
import getopt
import json
import urllib
import urllib2
from lxml import etree
import vavava
from vavava import util
from vavava import httputil
search_url = r'http://movie.douban.com/j/subject_suggest?q=%s'
search_page_url = r'http://movie.douban.com/subject_search?search_text=%s&cat=1002'

util.set_default_utf8()

class Search:
    def __init__(self):
        self.http = httputil.HttpUtil(charset='utf-8')
    def search(self, keyword):
        str = search_url%urllib2.quote(keyword)
        data = self.http.get(str)
        j = json.loads(data)
        for movie in j:
            if movie['type'] == 'movie':
                print '=============================================================='
                print 'Title: ', movie['title']
                print 'SubTitle: ', movie['sub_title']
                print 'year: ', movie['year']
                print 'url: ', movie['url']
                print 'img: ', movie['img']

import re
class SearchPage:
    def __init__(self):
        self.http = httputil.HttpUtil(charset='utf-8')
    def search(self, keyword):
        str = search_page_url%urllib.quote(keyword)
        data = self.http.get(str).decode('utf-8')
        tree = etree.HTML(data)
        movies = tree.xpath(r'//*[@id="content"]/div/div[1]/div[2]/table//div[@class="pl2"]')
        for movie in movies:
            try:
                children = movie.getchildren()
                a = children[0] # title
                url = a.get('href') # addr
                span = a.find('span') # alias
                p = movie.find(r'p[@class="pl"]') # score
                span_rating_nums = movie.find(r'div/span[@class="rating_nums"]')
                title = a.text
                if span is not None:
                    title = a.text + span.text
                print '========================================================'
                print title.replace(' ', '').replace('\n', '')
                print p.text
                if span_rating_nums is not None:
                    score = span_rating_nums.text
                    print score
                print url
            except:
                print '????????????'

def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """

if __name__ == "__main__":
    config = ''
    opts, args = getopt.getopt(sys.argv[1:], "c:h", ["--long-one"])
    for k, v in opts:
        if k in ("-h"):
            usage()
            exit(0)
        elif k in ("-c"):
            config = v
    if len(args) > 0:
        keywords = ''
        for x in args:
            keywords += x + ' '
        SearchPage().search(keywords)
    else:
        print 'keyword needed.'
    exit(0)
