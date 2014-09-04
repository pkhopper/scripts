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
    def __init__(self, config='miniaxel.ini'):
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
        # self.token = json.loads(self.cfg.get('login', 'token'))
        self.access_token = self.cfg.get('login', 'access_token')
        self.remind_in = self.cfg.get('login', 'remind_in')
        self.expires_at = self.cfg.getint('login', 'expires_at')
config = Config()

class Client(object):
    def __init__(self, api_key, api_secret, redirect_uri, uid=None,
                 access_token=None, remind_in=None, expires_at=None):
        # const define
        self.site = 'https://api.weibo.com/'
        self.authorization_url = self.site + 'oauth2/authorize'
        self.token_url = self.site + 'oauth2/access_token'
        self.api_url = self.site + '2/'

        # init basic info
        self.client_id = api_key
        self.client_secret = api_secret
        self.redirect_uri = redirect_uri
        self.uid = uid
        self.access_token = access_token
        self.remind_in = remind_in
        self.expires_at = expires_at

        self.session = requests.session()
        self.session.params = {'access_token': access_token}

    @property
    def authorize_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri
        }
        return "{0}?{1}".format(
            self.authorization_url, urllib.urlencode(params))

    @property
    def alive(self):
        if self.expires_at:
            return self.expires_at > time.time()
        else:
            return False

    def set_code(self, authorization_code):
        """Activate client by authorization_code.
        """
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        res = requests.post(self.token_url, data=params)
        token = json.loads(res.text)
        self._assert_error(token)

        self.uid = token['uid']
        self.access_token = token['access_token']
        self.expires_at = token['expires_at']

        token[u'expires_at'] = int(time.time()) + int(token.pop(u'expires_in'))
        self.session.params = {'access_token': self.access_token}

    def _assert_error(self, d):
        """Assert if json response is error.
        """
        if 'error_code' in d and 'error' in d:
            raise RuntimeError("{0} {1}".format(
                d.get("error_code", ""), d.get("error", "")))

    def get(self, uri, **kwargs):
        """Request resource by get method.
        """
        url = "{0}{1}.json".format(self.api_url, uri)
        res = json.loads(self.session.get(url, params=kwargs).text)
        self._assert_error(res)
        return res

    def post(self, uri, **kwargs):
        """Request resource by post method.
        """
        url = "{0}{1}.json".format(self.api_url, uri)
        if "pic" not in kwargs:
            res = json.loads(self.session.post(url, data=kwargs).text)
        else:
            files = {"pic": kwargs.pop("pic")}
            res = json.loads(self.session.post(url,
                                               data=kwargs,
                                               files=files).text)
        self._assert_error(res)
        return res

    def login(self):
        if config.access_token == '':
            print self.authorize_url
            config.code = raw_input('code=?')
            self.set_code(config.code)
            config.access_token = self.access_token
            config.remind_in = self.remind_in
            config.expires_at = self.expires_at
            config.cfg.set('login', 'code', config.code)
            config.cfg.set('login', 'access_token', config.access_token)
            config.cfg.set('login', 'remind_in'   , config.remind_in)
            config.cfg.set('login', 'expires_at'  , config.expires_at)
            config.cfg.write(open(config.cfg_file, 'w'))
        # client.post('statuses/update', status='python sdk test, check out http://lxyu.github.io/weibo/')

def test():
    client = Client(
            config.key,
            config.secret,
            config.callback,
            config.uid,
            config.access_token,
            config.remind_in,
            config.expires_at
        )
    client.login()
    print client.get('users/show', uid=config.uid)

def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """


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
