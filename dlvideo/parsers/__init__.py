#!/usr/bin/env python
# coding=utf-8

import sys
reload(sys).setdefaultencoding("utf8")
import tudou
import sohu
import w56
import iqiyi
import youku
import flvcd
import yytingting

def getVidPageParser(url):
    if url.find('sohu.com') > 0:
        return sohu.Sohu()
    elif url.find('tudou.com') > 0:
        return tudou.Tudou()
    elif url.find('56.com') > 0:
        return w56.W56()
    elif url.find('iqiyi.com') > 0:
        return iqiyi.Iqiyi()
    elif url.find('yytingting.com') > 0:
        return yytingting.Yytingting()
    else:
        return flvcd.FLVCD()

def getPlayListParser(url):
    if url.find('youku.com') > 0:
        return youku.YoukuPlaylist()
    if url.find('sohu.com') > 0:
        return sohu.SohuPlaylist()
