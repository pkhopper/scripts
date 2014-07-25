#!/usr/bin/env python

import re
import BeautifulSoup
from base_types import VidParserBase
from util import r1, unescape_html
from vavava.httputil import HttpUtil

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:30.0) Gecko/20100101 Firefox/30.0',
    # 'Referer': 'http://js.tudouui.com/bin/lingtong/PortalPlayer_108.swf',
    'DNT': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3'
}

def tudou_download_by_iid(iid, title):
    url = r'http://v2.tudou.com/f?id=' + iid + r'&sid=11000&hd=2&sj=1&areaCode=110000'
    xml = HttpUtil().get(url)
    xml = unescape_html(xml)
    url = BeautifulSoup.BeautifulSoup(xml).find('f').text
    return url, title, 'flv', 1, headers

# def tudou_download_by_id(id, title, merge=True):
#     html = get_html('http://www.tudou.com/programs/view/%s/' % id)
#     iid = r1(r'iid\s*=\s*(\S+)', html)
#     tudou_download_by_iid(iid, title, merge=merge)

def tudou_download(url):
    http = HttpUtil()
    html = http.get(url)
    html = html.decode(http.parse_charset())
    # iid = r1(r'iid\s*[:=]\s*(\d+)', html)
    iid = r1(r'"k":([^,]*),', html)
    assert iid
    title = r1(r"kw\s*[:=]\s*['\"]([^']+)['\"]", html)
    assert title
    title = unescape_html(title)
    return tudou_download_by_iid(iid, title)

def tudou_with_youku_info(url):
    http = HttpUtil()
    html = http.get(url)
    vcode = re.search(r'vcode\s*[:=]\s*\'([^\']+)\'', html)
    vcode = vcode.group(1)
    url = 'http://v.youku.com/v_show/id_{0}.html'.format(vcode)
    import flvcd
    return flvcd.FLVCD().info(url)


class Tudou(VidParserBase):
    def info(self, url, vidfmt=0):
        return tudou_download(url)


if __name__ == '__main__':
    url = r'http://www.tudou.com/programs/view/CLyCxUY7Tsg/'
    url = r'http://www.tudou.com/programs/view/hVT9-loKZ_M/'
    info = Tudou().info(url)
    print info

#
# def parse_playlist(url):
#     aid = r1('http://www.tudou.com/playlist/p/a(\d+)(?:i\d+)?\.html', url)
#     html = get_decoded_html(url)
#     if not aid:
#         aid = r1(r"aid\s*[:=]\s*'(\d+)'", html)
#     if re.match(r'http://www.tudou.com/albumcover/', url):
#         atitle = r1(r"title\s*:\s*'([^']+)'", html)
#     elif re.match(r'http://www.tudou.com/playlist/p/', url):
#         atitle = r1(r'atitle\s*=\s*"([^"]+)"', html)
#     else:
#         raise NotImplementedError(url)
#     assert aid
#     assert atitle
#     import json
#     #url = 'http://www.tudou.com/playlist/service/getZyAlbumItems.html?aid='+aid
#     url = 'http://www.tudou.com/playlist/service/getAlbumItems.html?aid='+aid
#     return [(atitle + '-' + x['title'], str(x['itemId'])) for x in json.loads(get_html(url))['message']]
#
# def tudou_download_playlist(url, create_dir=False, merge=True):
#     if create_dir:
#         raise NotImplementedError('please report a bug so I can implement this')
#     videos = parse_playlist(url)
#     for i, (title, id) in enumerate(videos):
#         print 'Downloading %s of %s videos...' % (i + 1, len(videos))
#         tudou_download_by_iid(id, title, merge=merge)
