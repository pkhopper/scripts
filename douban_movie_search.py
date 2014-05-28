#!/usr/bin/env python
# coding=utf-8

import sys
import getopt
import json
import urllib2
import vavava
from vavava import util
from vavava import httputil
search_url = r'http://movie.douban.com/j/subject_suggest?q=%s'

class Search:
    def __init__(self):
        self.http = httputil.HttpUtil(charset='utf-8')
    def search(self, keyword):
        str = search_url%urllib2.quote(keyword.strip())
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
        Search().search(keywords)
    else:
        print 'keyword needed.'
    exit(0)
