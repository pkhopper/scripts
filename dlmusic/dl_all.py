#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from dlmusic import songsdb

reload(sys)
sys.setdefaultencoding('utf-8')
import os
import re
import urllib
import urllib2
import cookielib

###### config ##########
if os.path.islink(__file__):
    __file__ = os.path.realpath(__file__)
g_currt_dir = os.path.dirname(__file__)
g_email     = r''
g_password  = r''
g_list_file = r''
g_db_file   = r''
g_outpath   = r''

def init():
    global g_email
    global g_password
    global g_list_file
    global g_db_file
    global g_outpath
    os.chdir(g_currt_dir)
    import ConfigParser
    cfg = ConfigParser.ConfigParser()
    cfg.read(r'config.ini')
    section = 'main'
    g_email     = cfg.get(section, 'email')
    g_password  = cfg.get(section, 'password')
    g_list_file = cfg.get(section, 'song_list')
    g_db_file   = cfg.get(section, 'db')
    g_outpath   = cfg.get(section, 'out_path')
    # print r'%s,%s,%s,%s,%s'%(g_email, g_password, g_list_file, g_db_file, g_outpath)

###### config (end) ##########

display = lambda x: sys.stdout.write('[***dl_all***] %s\n' % x)

HEADERS = {
    'User-Agent':      'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',
    'Referer':         'http://www.xiami.com/song/play',
}
def get_response(url):
    request = urllib2.Request(url)
    for header in HEADERS:
        request.add_header(header, HEADERS[header])

    try:
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.URLError as e:
        println(e)
        return ''


class Xiami:
    def __init__(self):
        self.email     = g_email     
        self.password  = g_password  
        self.list_file = g_list_file
        self.db_file   = g_db_file
        self.db        = songsdb.Songs(self.db_file)
        self.outpath   = g_outpath
        self.login()        

    def login(self):
        # Init
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        urllib2.install_opener(opener)
        # Login
        login_url = 'http://www.xiami.com/member/login'
        login_data = urllib.urlencode({
            'done': '/',
            'email':self.email,
            'password':self.password,
            'submit':'登 录',
        })
        login_headers = {
            'Referer':'http://www.xiami.com/web/login',
            'User-Agent':'Opera/9.60',
        }
        login_request = urllib2.Request(login_url, login_data, login_headers)
        response = urllib2.urlopen(login_request)
        login_response = response.read()
        return login_response

    def refresh_list(self):
        page_format = r'http://www.xiami.com/space/lib-song/u/2276125/page/%d'
        reg = re.compile(r'title="([^"]*)"\s*href="http://www.xiami.com/song/(\d*)')
        song_num = 0
        for i in xrange(1, 100):
            url = page_format%(i)
            display(url)
            html = get_response(url).decode(r'utf-8')
            results = reg.findall(html)
            if len(results) == 0:
                break
            for result in results:
                if not self.db.getinfo_by_code(result[1]):
                    self.db.insert(result[1], result[0])
                    song_num += 1
                else:
                    display('new:%d'%song_num)
                    return
            display('song_num:%d'%song_num)
        display('new:%d'%song_num)

    def dl(self):
        ids = [ row[1] for row in self.db.get_need_offline_list() ]
        for code in ids:
            cmd = r'python xiami.py --directory %s -s %s' % (self.outpath, code)
            display(cmd)
            os.system(cmd)
            self.db.set_offline(code, offline=1)

if __name__ == "__main__":
    init()
    print r'%s,%s,%s,%s,%s'%(g_email, g_password, g_list_file, g_db_file, g_outpath)
    xiami = Xiami()
    if xiami.login():
        if raw_input('refresh list?[y/n]') == 'y':
            xiami.refresh_list()
        if raw_input('download?[y/n]') == 'y':
            xiami.dl()
    else:
        print "sorry"

