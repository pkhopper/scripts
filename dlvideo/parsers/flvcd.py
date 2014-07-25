#!/usr/bin/env python

from urllib import quote
from re import findall
from vavava.httputil import HttpUtil
from base_types import VidParserBase
import vavava.util
vavava.util.set_default_utf8()


class FLVCD(VidParserBase):
    def info(self, url, vidfmt):
        parse_url = 'http://www.flvcd.com/parse.php?'
        parse_url += 'kw='+ quote(url)
        parse_url += '&flag=one'
        format = ['', 'high', 'super', 'real']
        if vidfmt > 0:
            parse_url += '&format=%s'%format[vidfmt]
        http = HttpUtil()
        http.add_header('Referer', parse_url)
        html = http.get(parse_url).decode('gb2312')
        try:
            import BeautifulSoup
            soup = BeautifulSoup.BeautifulSoup(html)
            m3u = soup.find('input', attrs={'name': 'inf'}).get('value')
            title = soup.find('input', attrs={'name': 'name'}).get('value')
        except:
            raise ValueError('say "not support."')
        urls = [url for url in m3u.split('|')]
        return urls, title, None, 5, None

def test():
    url = r'http://www.iqiyi.com/dianshiju/20120730/9682f22c54d70f29.html'
    url = r'http://www.tudou.com/programs/view/hVT9-loKZ_M/'
    url = r'http://v.youku.com/v_show/id_XNzQzNTc0Nzgw.html'
    flvcd = FLVCD()
    flvcd.info(url, 0)


if __name__ == '__main__':
    test()



