#!/usr/bin/env python

from urllib import quote
from vavava.httputil import HttpUtil
from base_types import VidParserBase
import vavava.util
vavava.util.set_default_utf8()

def host_filter(url):
    # http://video.sina.com.cn/p/ent/v/m/2014-08-14/102164094039.html
    if url.find('video.sina.com.cn') > 0:
        return 1, {'Referer': url, 'DNT': '1'}
    return 3, None

class FLVCD(VidParserBase):
    def info(self, url, vidfmt):
        parse_url = 'http://www.flvcd.com/parse.php?'
        parse_url += 'kw='+ quote(url)
        parse_url += '&flag=one'
        format = ['', 'high', 'super', 'real']
        if vidfmt > 0:
            parse_url += '&format=%s'%format[vidfmt]
        parse_url += "&Go=1&go=1"  # 20150723
        http = HttpUtil()
        http.add_header('Referer', parse_url)
        print parse_url
        try:
            html = http.get(parse_url).decode('gb2312', 'ignore')
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html)
            m3u = soup.find('input', attrs={'name': 'inf'}).get('value')
            title = soup.find('input', attrs={'name': 'name'}).get('value')
        except Exception as e:
            # raise ValueError('not support')
            return [], '', None, 0, None
        urls = [u for u in m3u.split('|')]
        npf, headers = host_filter(url)
        return urls, title, None, npf, headers

def test():
    url = r'http://video.sina.com.cn/p/ent/v/m/2014-08-14/102164094039.html'
    flvcd = FLVCD()
    print flvcd.info(url, 0)


if __name__ == '__main__':
    test()



