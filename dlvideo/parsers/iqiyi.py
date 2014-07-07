#!/usr/bin/env python

import json
from vavava import httputil
from base_types import *

class Iqiyi():
    def __init__(self):
        self.http = httputil.HttpUtil()

    def real_url(self, url):
        import time
        return json.loads(get_html(url[:-3]+'hml?v='+str(int(time.time()) + 1921658928)))['l'] # XXX: what is 1921658928?

    def info(self, url, vidfmt):
        headers = {
            'Referer': 'http://www.iqiyi.com/player/20140626170254/Player.swf',
            'User-Agent': r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:30.0) Gecko/20100101 Firefox/30.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        html = self.http.get(url, headers=headers)
        videoId = r1(r'''data-player-videoid\s*[:=]\s*["']([^"']*)["']''', html)
        info_url = r'http://cache.video.qiyi.com/vms?key=fvip&src=p&vid={}'.format(videoId)
        html = self.http.get(info_url, headers=headers)
        vstream = json.loads(html)['data']['vp']
        # du = 'http://data.video.qiyi.com'
        # nvid = e2847b3b9b81469cbf7247ee8a1da61f
        du, dts, nvid = vstream['du'], vstream['dts'], vstream['nvid']
        for vs in vstream['tkl'][0]['vs']:
            for fs in vs['fs']:
                b, d, l, msz = fs['b'], fs['d'], fs['l'], fs['msz']
                real_url = 'http://data.video.qiyi.com/{}/videos{}'.format(nvid, l)
                addr = html = self.http.get(real_url, headers=headers)
                print addr
        info_url = 'http://cache.video.qiyi.com/v/%s/%s/%s/' % (videoId, pid, ptype)
        return info_url

def iqiyi_download(url, merge=True):
    # html = get_html(url)
    # #title = r1(r'title\s*:\s*"([^"]+)"', html)
    # #title = unescape_html(title).decode('utf-8')
    # #videoId = r1(r'videoId\s*:\s*"([^"]+)"', html)
    # #pid = r1(r'pid\s*:\s*"([^"]+)"', html)
    # #ptype = r1(r'ptype\s*:\s*"([^"]+)"', html)
    # #info_url = 'http://cache.video.qiyi.com/v/%s/%s/%s/' % (videoId, pid, ptype)
    # videoId = r1(r'''data-player-videoid\s*[:=]\s*["']([^"']*)["']''', html, flag=re.I)
    # assert videoId
    # info_url = 'http://cache.video.qiyi.com/v/%s' % videoId

    info_url = Iqiyi().get_info_url(url)
    info_xml = get_html(info_url)

    from xml.dom.minidom import parseString
    doc = parseString(info_xml)
    title = doc.getElementsByTagName('title')[0].firstChild.nodeValue
    size = int(doc.getElementsByTagName('totalBytes')[0].firstChild.nodeValue)
    urls = [n.firstChild.nodeValue for n in doc.getElementsByTagName('file')]
    assert urls[0].endswith('.f4v'), urls[0]
    urls = map(real_url, urls)
    download_urls(urls, title, 'flv', total_size=size, merge=merge)

def test():
    url = r'http://www.iqiyi.com/dianshiju/20120730/9682f22c54d70f29.html'
    qiyi = Iqiyi()
    qiyi.get_info_url(url)


if __name__ == '__main__':
    test()



