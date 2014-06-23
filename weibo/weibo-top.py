#!/usr/bin/env python
# coding=utf-8

import sys
import getopt
import json
import my_weibo


weibo = my_weibo.MyWeibo()
weibo.login()

def display_user_timeline():
    timeline = weibo.client.statuses.user_timeline.get()
    for pos, status in enumerate(timeline.statuses):
        print '[%3d=%s] %s' % (pos, status.created_at, status.text)

def display_public_timeline():
    timeline = weibo.client.statuses.public_timeline.get()
    for pos, status in enumerate(timeline.statuses):
        print '[%3d=%s] %s' % (pos, status.created_at, status.text)

def post(msg, pic_file=None):
    if pic_file:
        pic = open(pic_file)
    else:
        pic = None
    weibo.client.statuses.upload.post(status=msg, pic=pic)

def statuses():
    status = weibo.client.statuses
    print status

def usage():
    print \
        """
usage:
    ./weibo-top [-h] [c configfile]
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
        elif k in ("--long-one"):
            pass

    # statuses()
    display_public_timeline()

