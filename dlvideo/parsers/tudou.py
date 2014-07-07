#!/usr/bin/env python

from base_types import VidParserBase
from util import r1, unescape_html
from vavava.httputil import HttpUtil

def tudou_download_by_iid(iid, title, refer, merge=True):
    url = r'http://v2.tudou.com/f?id=' + iid + r'&sid=11000&hd=2&sj=1'
    xml = HttpUtil().get(url)
    xml = unescape_html(xml)
    url = r1(r'<f[^>]*>([^<]*)<', xml)
    # download_urls([url], title, 'flv', total_size=None, merge=merge)
    return [url], title, 'flv'

# def tudou_download_by_id(id, title, merge=True):
#     html = get_html('http://www.tudou.com/programs/view/%s/' % id)
#     iid = r1(r'iid\s*=\s*(\S+)', html)
#     tudou_download_by_iid(iid, title, merge=merge)

def tudou_download(url, merge=True):
    http = HttpUtil()
    html = http.get(url)
    html = html.decode(http.parse_charset())
    # iid = r1(r'iid\s*[:=]\s*(\d+)', html)
    iid = r1(r'"k":([^,]*),', html)
    assert iid
    title = r1(r"kw\s*[:=]\s*['\"]([^']+)['\"]", html)
    assert title
    title = unescape_html(title)
    return tudou_download_by_iid(iid, title, refer=url, merge=merge)

class Tudou(VidParserBase):
    def info(self, url, vidfmt=0):
        return tudou_download(url)

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
