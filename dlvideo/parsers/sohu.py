
#!/usr/bin/env python
# coding=utf-8

from util import *
from base_types import VidParserBase, PlayListFilterBase
from vavava.httputil import HttpUtil

def real_url(host, prot, file, new):
    url = 'http://%s/?prot=%s&file=%s&new=%s' % (host, prot, file, new)
    html = HttpUtil().get(url)
    start, _, host, key, _, _, _, _, _ = html.split('|')
    return '%s%s?key=%s' % (start[:-1], new, key)

class Sohu(VidParserBase):
    def info(slef, url, merge=True, vidfmt=0):
        """ format_op = ["norVid", "highVid", "superVid", "oriVid"] """
        assert vidfmt in (0, 1, 2, 3)
        http = HttpUtil()
        vid_page = http.get(url)
        vid = r1('vid="(\d+)"', vid_page)
        if not vid:
            vid = r1('vid:\s*\'(\d+)\'', vid_page)
        assert vid
        import json
        html = http.get('http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid)
        data = json.loads(html.decode(http.parse_charset()))
        if vidfmt > 0:
            format_op = ["norVid", "highVid", "superVid", "oriVid"]
            vid = data['data'][format_op[vidfmt]]
            html = http.get('http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid)
            data = json.loads(html.decode(http.parse_charset()))
        host = data['allot']
        prot = data['prot']
        urls = []
        data = data['data']
        title = data['tvName']
        size = sum(data['clipsBytes'])
        assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
        for file, new in zip(data['clipsURL'], data['su']):
            urls.append(real_url(host, prot, file, new))
        assert data['clipsURL'][0].endswith('.mp4')
        return urls, title, 'mp4', 5, None

class SohuPlaylist(PlayListFilterBase):
    def info(self, url):
        if url.find('sohu.com') < 0:
            raise ValueError('not a sohu.com video url')
        import json
        import re
        html = HttpUtil().get(url)
        playlistid = re.findall(r'var playlistId="(?P<s>[^"]*?)";', html)[0]
        url = r'http://pl.hd.sohu.com/videolist?playlistid=%s'%playlistid
        data = json.loads(HttpUtil().get(url), encoding='gbk')
        title = data['albumName']
        items = [video['pageUrl'] for video in data['videos']]
        return title, items

if __name__ == "__main__":
    url = "http://my.tv.sohu.com/us/42891366/72351551.shtml"
    info = Sohu().info(url, vidfmt=0)
    print info