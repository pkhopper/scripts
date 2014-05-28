#!/usr/bin/env python
# coding=utf-8

import os
import sys
import getopt
from douban_client import DoubanClient

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
        cfg = ConfigParser.ConfigParser()
        cfg.read(pjoin(curr_dir, config))
        self.key = cfg.get('login', 'key')
        self.code = cfg.get('login', 'code')
        self.secret = cfg.get('login', 'secret')
        self.callback = cfg.get('login', 'callback')
        self.scope = cfg.get('login', 'SCOPE')
        self.user = cfg.get('login', 'user')
        self.password = cfg.get('login', 'password')
        self.token = cfg.get('login', 'token')
        self.refresh_token = cfg.get('login', 'refresh_token')
config = Config()

KEY = config.key
SECRET = config.secret
CALLBACK = config.callback
CODE = config.code
SCOPE = config.scope
user_email = config.user
user_password = config.password
TOKEN = config.token

class MyDouban:
    def __init__(self):
        self.clent = DoubanClient(KEY, SECRET, CALLBACK, SCOPE)
        self.clent.auth_with_token(TOKEN)

    def search_movie(self, keyword):
        q = ''
        for kw in keyword:
            q += kw + ''
        return self.clent.movie.search(q)

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

    douban = MyDouban()
    print douban.clent.user.me
    print douban.search_movie(args)
