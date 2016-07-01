#!/usr/bin/env python
# coding=utf-8

import os
from vavava import util
from vavava import httputil

util.set_default_utf8()
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

total = 0

def geturls():
    url = r"http://www.bjchs.org.cn/map/Org_infoList?key_area_code=%s"
    ids = [id for id in xrange(0, 20)]
    urls = [url%(10000 + id)  for id in ids]
    return urls

def getmatches(string):
    regstr = """机构名称：\s*([^\<]*)[^\<]*\</p>[^\>]+>机构地址：\s*([^\<]*)[^\<]*\</p>[^\>]+>区县：\s*([^\<]*)[^\<]*\</p>[^\>]+>机构电话：\s*([^\<]*)[^\<]*\</p>[^\>]+>基本医保点：\s*([^\<]*)[^\<]*\</p>[^\>]+>医保编码：\s*([^\<]*)[^\<]*\</p>[^\>]+>新农合定点：\s*([^\<]*)[^\<]*\</p>[^\>]+>邮政编码：\s*([^\<]*)[^\<]*\</p>[^\>]+>"""
    matches = util.reg_helper(string, regstr)
    return matches

def save(matches, num):
    with open("%d.txt"%num, "w") as f:
        f.write("%s,%s,%s,%s,%s,%s,%s,%s,\n"%("机构名称", "机构地址", "区县", "机构电话", "基本医保点", "医保编码", "新农合定点", "邮政编码"))
        for match in matches:
            line = "%s,%s,%s,%s,%s,%s,%s,%s,\n"%match
            f.write(line)
            global total
            total += 1

if __name__ == "__main__":
    log = util.get_logger()
    try:
        i = 0
        for url in geturls():
            content = httputil.http_get(url)
            matches = getmatches(content)
            save(matches, i)
            i += 1
        print total
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        log.exception(e)

