#!/usr/bin/env python

from re import search
from base_types import *
from util import *
from vavava.httputil import HttpUtil
import json

def w56_download_by_id(id, refer, vidfmt=0, merge=True):
    html = HttpUtil().get('http://vxml.56.com/json/%s/?src=site'%id)
    info = json.loads(html)['info']
    title = info['Subject']
    # assert title
    # hd = info['hd']
    # assert hd in (0, 1, 2)
    # type = ['normal', 'clear', 'super'][hd]
    assert vidfmt in (0, 1, 2)
    type = ['normal', 'clear', 'super'][vidfmt]
    files = [x for x in info['rfiles'] if x['type'] == type]
    assert len(files) == 1
    size = int(files[0]['filesize'])
    url = files[0]['url']
    ext = r1(r'\.([^.]+)\?', url)
    assert ext in ('flv', 'mp4')
    return [url], title, str(ext), 1, None

def w56_download(url, vidfmt):
    # id = r1(r'http://www.56.com/u\d+/v_(\w+).html', url)
    id = r1(r'[-|_]+(\w+).html', url)
    return w56_download_by_id(id, url, vidfmt=vidfmt)

class W56(VidParserBase):
    def info(self, url, vidfmt=0):
        return w56_download(url, vidfmt=vidfmt)

if __name__ == '__main__':
    url = r'http://www.56.com/u92/v_NDgzNzQ3Mzc.html'
    url = r'http://www.56.com/w99/play_album-aid-9904987_vid-NjgxODA5NTI.html'
    print W56().info(url)
