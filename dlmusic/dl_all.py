#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import re
import urllib
import urllib2
import cookielib
import songsdb

###### config ##########
pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']

class Config:
    def __init__(self, config='config.ini'):
        dump_path = lambda path: path.replace(r"%(home)s", user_path)
        if os.path.islink(__file__):
            curr_dir = dirname(abspath(os.readlink(__file__)))
        else:
            curr_dir = dirname(abspath(__file__))
        import ConfigParser
        cfg = ConfigParser.ConfigParser()
        cfg.read(pjoin(curr_dir, config))
        self.email     = cfg.get('main', 'email')
        self.password  = cfg.get('main', 'password')
        self.list_file = cfg.get('main', 'song_list')
        self.db_file   = cfg.get('main', 'db')
        self.outpath   = cfg.get('main', 'out_path')
config = Config()
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
        print e
        return ''


class Xiami:
    def __init__(self):
        self.email     = config.email
        self.password  = config.password
        self.list_file = config.list_file
        self.db_file   = config.db_file
        self.outpath   = config.outpath
        self.db        = songsdb.Songs(self.db_file)
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
    print r'%s,%s,%s,%s,%s'%(
        config.email,
        config.password,
        config.list_file,
        config.db_file,
        config.outpath)
    xiami = Xiami()
    if xiami.login():
        if raw_input('refresh list?[y/n]') == 'y':
            xiami.refresh_list()
        if raw_input('download?[y/n]') == 'y':
            xiami.dl()
    else:
        print "sorry"

