#!/usr/bin/env python
# coding=utf-8

import tudou
import sohu
import w56
import iqiyi
import youku

def getVidPageParser(url):
    if url.find('sohu.com') > 0:
        return sohu.Sohu()
    elif url.find('tudou.com') > 0:
        return tudou.Tudou()
    elif url.find('56.com') > 0:
        return w56.W56()
    elif url.find('iqiyi.com') > 0:
        return iqiyi.Iqiyi()
    else:
        raise NotImplementedError(url)

def getPlayListParser(url):
    if url.find('youku.com') > 0:
        return youku.YoukuPlaylist()
    if url.find('sohu.com') > 0:
        return sohu.SohuPlaylist()
