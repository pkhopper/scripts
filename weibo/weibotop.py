#!/usr/bin/env python
# coding=utf-8

import datetime
import os
pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']

import util

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
        self.access_token = self.cfg.get('login', 'access_token')
        self.remind_in = self.cfg.get('login', 'remind_in')
        self.expires_at = self.cfg.getint('login', 'expires_at')

from snspy import APIClient
from snspy import SinaWeiboMixin

class MyWeibo:
    """ http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI """
    def __init__(self, config='miniaxel.ini'):
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

    def get_friends_timeline(self):
        result = self.client.statuses.friends_timeline.get()
        return result

    def post(self, msg, pic_file=None):
        if pic_file:
            pic = open(pic_file)
        else:
            pic = None
        self.client.statuses.upload.post(status=msg, pic=pic)

###########
def parse_uc_date(str):
    MONTHS   = [("Jan", "January"),
                ("Feb", "February"),
                ("Mar", "March"),
                ("Apr", "April"),
                ("May", "May"),
                ("Jun", "June"),
                ("Jul", "July"),
                ("Aug", "August"),
                ("Sep", "September"),
                ("Oct", "October"),
                ("Nov", "November"),
                ("Dec", "December")]
    for month in MONTHS:
        if str.find(month[0]) > 0:
            str =str.replace(month[0], month[1])
    format = '%a %B %d %H:%M:%S +0800 %Y'
    date = datetime.datetime.strptime(str, format)
    return date - datetime.timedelta(hours=8)

def display_friends_timeline(weibo):
    timeline = weibo.get_friends_timeline()
    pos = len(timeline.statuses)
    for status in reversed(timeline.statuses):
        pos -= 1
        print '[%03d] %s %s' % (pos, status.user.screen_name,
            util.nice_date(parse_uc_date(status.created_at)))
        print '\t%s' % (status.text)
        print '\thttp://www.weibo.com/{}/{}'.format(
            status.user.idstr, util.mid_to_url(status.mid))

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
    parser.add_argument('-c', '--config', default='miniaxel.ini')
    args = parser.parse_args()
    print 'args===>{}'.format(args)
    return args

if __name__ == "__main__":
    args = parse_args()
    weibo = MyWeibo(args.config)
    weibo.login()
    test(weibo)
    # statuses(weibo)
    display_friends_timeline(weibo)
