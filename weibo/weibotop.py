#!/usr/bin/env python
# coding=utf-8

import os
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

from snspy import APIClient
from snspy import SinaWeiboMixin

class MyWeibo:
    """ http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI """
    def __init__(self, config='config.ini'):
        self.cfg = Config(config)

    def login(self):
        if self.cfg.access_token == '':
            self.client = APIClient(
                SinaWeiboMixin,
                self.cfg.key,
                self.cfg.secret,
                self.cfg.callback
            )
            url = self.client.get_authorize_url()
            print url
            code = raw_input('code=?')
            r = self.client.request_access_token(code)
            self.cfg.access_token = self.client.access_token
            self.cfg.remind_in = self.client.remind_in
            self.cfg.expires_at = self.client.expires_at
            self.cfg.cfg.set('login', 'code',         self.cfg.code        )
            self.cfg.cfg.set('login', 'access_token', self.cfg.access_token)
            self.cfg.cfg.set('login', 'remind_in'   , self.cfg.remind_in   )
            self.cfg.cfg.set('login', 'expires_at'  , self.cfg.expires_at  )
            self.cfg.cfg.write(open(self.cfg.cfg_file, 'w'))
        else:
            self.client = APIClient(
                SinaWeiboMixin,
                self.cfg.key,
                self.cfg.secret,
                self.cfg.callback,
                self.cfg.access_token,
                self.cfg.expires_at
            )
        self.screen_name = self.client.users.show.get(uid=self.cfg.uid)['screen_name']

    def get_pub_timeline(self):
        return self.client.statuses.public_timeline.get().statuses

    def post(self, msg, pic_file=None):
        if pic_file:
            pic = open(pic_file)
        else:
            pic = None
        self.client.statuses.upload.post(status=msg, pic=pic)

###########
def display_public_timeline(weibo):
    for pos, status in enumerate(weibo.get_pub_timeline()):
        print '[%03d] %s' % (pos, status.created_at)
        print '\t%s' % (status.text)

def statuses(weibo):
    status = weibo.client.statuses
    print status


def test(weibo):
    print weibo.screen_name
    # print weibo.client.statuses.user_timeline.get()
    # print weibo.client.statuses.update.post(status=u'test plain weibo')
    # print weibo.client.statuses.upload.post(status=u'test weibo with picture', pic=open('/Users/michael/test.png'))

def parse_args():
    usage = """./weibo-top [-h] [-c configfile]"""
    import argparse
    parser=argparse.ArgumentParser(usage=usage, description='top-like weibo', version='0.1')
    parser.add_argument('-c', '--config', default='config.ini')
    args = parser.parse_args()
    print 'args===>{}'.format(args)
    return args

if __name__ == "__main__":
    args = parse_args()
    weibo = MyWeibo(args.config)
    weibo.login()
    test(weibo)
    # statuses(weibo)
    display_public_timeline(weibo)
