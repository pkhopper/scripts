#!/usr/bin/python
# thx, cp from http://www.tuicool.com/articles/eaeUVz

import urllib2,sys
from HTMLParser import HTMLParser
from vavava import util
util.set_default_utf8()


class MyHTMLParser(HTMLParser):
    def  __init__(self):
        HTMLParser.__init__(self)
        self.t=False
        self.pronouce = []
        self.trans=[]
        self.pr=False

    def handle_starttag(self, tag, attrs):
        if tag=='div':
            for attr in attrs:
                if attr==('class','hd_prUS') or \
                 attr==('class','hd_pr'):
                    self.pr=True
        if tag=='span':
            for attr in attrs:
                if attr==('class','def'):
                    self.t=True

    def handle_data(self, data):
        if self.t:
            self.trans.append(data)
            self.t=False
        if self.pr:
            self.pronouce.append(data)
            self.pr=False
    def getTrans(self):
        return self.trans


class Trans:
    _URL='http://cn.bing.com/dict/search'
    def __init__(self):
        self.url=Trans._URL+"?q=%s&go=&qs=bs&form=CM&mkt=zh-CN&setlang=ZH"
        self.html=None

    def trans(self, w):
        self.getHtml(w)
        return self.parseHtml()

    def getHtml(self,word):
        self.url=self.url %word
        req = urllib2.Request(self.url)
        fd=urllib2.urlopen(req)
        self.html=fd.read()
        self.html=unicode(self.html,'utf-8')
        fd.close()

    def parseHtml(self):
        parser = MyHTMLParser()
        self.html=parser.unescape(self.html)
        parser.feed(self.html)
        string = ''
        for i, s in enumerate(parser.getTrans()):
            string += "%s. %s\n" % (i, s)
        return string

if __name__=='__main__':
    print Trans().trans(sys.argv[1])