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

client = DoubanClient(KEY, SECRET, CALLBACK, SCOPE)

def auth_with_code():
    print client.authorize_url
    client.auth_with_code(CODE)

def auth_with_password():
    client.auth_with_password(user_email, user_password)

def auth_with_token():
    client.auth_with_token(TOKEN)


if __name__ == "__main__":
    auth_with_token()
    print client.user.me
