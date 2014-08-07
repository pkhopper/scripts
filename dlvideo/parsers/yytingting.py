#!/usr/bin/env python

from urllib import quote
from vavava.httputil import HttpUtil
from base_types import VidParserBase
import util as _util
import vavava.util
vavava.util.set_default_utf8()
# http://www.yytingting.com/#/bookstore/bookDetail.jsp?bookId=126
import json

class Yytingting(VidParserBase):
    def info(self, url, vidfmt):
        try:
            return self.__info(url, vidfmt)
        except Exception as e:
            raise e

    def __info(self, url, vidfmt):
        parse_url = 'http://www.yytingting.com/bookstore/playAndDownload.action?' \
                    'id=%s&pageNo=%d&pageSize=%d'
        id = _util.r1('bookId=(\d+)', url)
        http = HttpUtil()
        http.add_header('Referer', url)
        tmp = parse_url % (id, 1, 20)
        info = http.get(tmp)
        js = json.loads(info)
        data = js['data']['data']
        pageNo = js['data']['pageNo']
        pageSize = js['data']['pageSize']
        total = js['data']['total']

        urls1 = []
        for i in range(total/pageSize):
            url = parse_url % (id, i+1, pageSize)
            html = http.get(url)
            js = json.loads(html)
            fmt = 'http://www.yytingting.com/resource/getPlayUrl.action?id=%d&type=6'
            urls1 = urls1 + [(data['resName'], fmt % data['resId']) for data in js['data']['data']]

        urls = []
        for name, url in urls1:
            html = http.get(url)
            js = json.loads(html)
            urls.append((name, js['data']['url']))
        return urls


def test():
    url = r'http://www.iqiyi.com/dianshiju/20120730/9682f22c54d70f29.html'
    url = r'http://www.tudou.com/programs/view/hVT9-loKZ_M/'
    url = r'http://v.youku.com/v_show/id_XNzQzNTc0Nzgw.html'
    url = r'http://www.yytingting.com/#/bookstore/bookDetail.jsp?bookId=126'
    yytingting = Yytingting()
    urls = yytingting.info(url, 0)
    urls = ['%s.mp3,%s\n' %(data[0], data[1]) for data in urls]
    with open('urls.txt', 'w') as fp:
        fp.writelines(urls)


if __name__ == '__main__':
    test()



