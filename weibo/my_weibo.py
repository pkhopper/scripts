#!/usr/bin/env python
# coding=utf-8

import os
import sys
import getopt
import json
import time
import urllib
import requests


pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']

class Config:
    def __init__(self, config='config.ini'):
        dump_path = lambda path: path.replace(r"%(home)s", user_path)
        if os.path.islink(__file__):
            curr_dir = dirname(abspath(os.readlink(__file__)))
        else:
            curr_dir = dirname(abspath(__file__))
        import ConfigParser
        self.cfg_file = pjoin(curr_dir, config)
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(self.cfg_file)
        self.uid = self.cfg.get('login', 'uid')
        self.key = self.cfg.get('login', 'key')
        self.code = self.cfg.get('login', 'code')
        self.secret = self.cfg.get('login', 'secret')
        self.callback = self.cfg.get('login', 'callback')
        self.access_token = self.cfg.get('login', 'access_token')
        self.remind_in = self.cfg.get('login', 'remind_in')
        self.expires_at = self.cfg.getint('login', 'expires_at')
config = Config()

from snspy import APIClient
from snspy import SinaWeiboMixin

class MyWeibo:
    """ http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI """

    def login(self):
        if config.access_token == '':
            self.client = APIClient(
                SinaWeiboMixin,
                config.key,
                config.secret,
                config.callback
            )
            url = self.client.get_authorize_url()
            print url
            code = raw_input('code=?')
            r = self.client.request_access_token(code)
            config.access_token = self.client.access_token
            config.remind_in = self.client.remind_in
            config.expires_at = self.client.expires_at
            config.cfg.set('login', 'code',         config.code        )
            config.cfg.set('login', 'access_token', config.access_token)
            config.cfg.set('login', 'remind_in'   , config.remind_in   )
            config.cfg.set('login', 'expires_at'  , config.expires_at  )
            config.cfg.write(open(config.cfg_file, 'w'))
        else:
            self.client = APIClient(
                SinaWeiboMixin,
                config.key,
                config.secret,
                config.callback,
                config.access_token,
                config.expires_at
            )

def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """

def test():
    weibo = MyWeibo()
    weibo.login()
    print weibo.client.statuses.user_timeline.get()
    print weibo.client.statuses.update.post(status=u'test plain weibo')
    # print weibo.client.statuses.upload.post(status=u'test weibo with picture', pic=open('/Users/michael/test.png'))

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "c:h", ["--long-one"])
    for k, v in opts:
        if k in ("-h"):
            usage()
            exit(0)
        elif k in ("-c"):
            config = v
        elif k in ("--long-one"):
            pass
    test()
