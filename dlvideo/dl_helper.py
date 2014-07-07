#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
util.set_default_utf8()

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']


default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

log = util.get_logger()

def to_native_string(s):
    if type(s) == unicode:
        return s.encode(default_encoding)
    else:
        return s

def escape_file_path(path):
    path = path.replace('/', '_')
    path = path.replace('\\', '_')
    path = path.replace('*', '_')
    path = path.replace('?', '_')
    path = path.replace('\'', '_')
    return path

def dl_methods(url, file_name, refer=None, nthread=10, nperfile=True):
    if os.path.isfile(file_name):
        log.info("download file exists, abort.: %s", file_name)
        return
    # 3 methods to download url
    tmp_file = file_name + '!'
    result = 0
    if not nperfile:
        # 1:
        result = Wget().get(url=url, out=tmp_file, referer=refer)
    else:
        # 2:
        result = Axel().get(url=url, out=tmp_file, n=nthread, referer=refer)
    # 3
    # print 'Downloading %s ...' % filename
    # url_save(url, tmp_file, bar, refer=refer)
    # bar.done()
    os.rename(tmp_file, file_name)
    return result


def download_urls(urls, title, ext, odir='.', nthread=10,
                  nperfile=True, refer=None, merge=True):
    title = to_native_string(title)
    origin_title = title
    title = escape_file_path(title)
    origin_title = '%s.%s' % (origin_title, ext)
    filename = '%s.%s' % (title, ext)
    origin_title = pjoin(odir, origin_title)
    file_name = pjoin(odir, filename)
    if os.path.exists(origin_title) or os.path.exists(file_name):
        log.info('out put file exists, %s', origin_title)
        return
    files = []
    # print 'Downloading %s.%s ...' % (title, ext)
    tmp_path = pjoin(odir, '.dlvideo')
    util.assure_path(tmp_path)
    if len(urls) > 1:
        for i, url in enumerate(urls):
            filename = '%s[%02d-%02d].%s' % (title, len(urls), i, ext)
            tmp_file = pjoin(tmp_path, filename)
            files.append(tmp_file)
            print '[dl] %s'%(url)
            dl_methods(url, tmp_file, refer=refer, nthread=10, nperfile=True)
        if merge:
            if ext == 'flv':
                from flv_join import concat_flvs
                concat = concat_flvs
            elif ext == 'mp4':
                from mp4_join import concat_mp4s
                concat = concat_mp4s
            else:
                log.error("Can't join files: {}".format(files))
                return
            concat(files, file_name)
            for f in files:
                os.remove(f)
    else:
        dl_methods(urls[0], file_name=file_name, refer=refer, nthread=10, nperfile=True)
        print 'ok'
    os.rename(file_name, origin_title)

class Wget:
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 Safari/537.36'
    def get(self, url, out=None, referer=None, proxy=None):
        cmd = "wget -c --user-agent='%s'"%(self.useragent)
        if referer:
            cmd += " --referer='%s'"%(referer)
        if out:
            cmd += " --output-document='%s'"%(out)
        if not proxy:
            cmd += " --no-proxy"
        cmd += " '%s'"%(url)
        print cmd
        return os.system(cmd)


class Axel:
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 Safari/537.36'

    def get(self, url, out=None, n=None, referer=None):
        cmd = "axel -v -a -U '%s'"%(self.useragent)
        if referer:
            cmd += " -H 'Referer:%s'"%(referer)
        if n:
            cmd += " -n %d"%(n)
        if out:
            cmd += " -o '%s'"%(out)
        cmd += " '%s'"%(url)
        print cmd
        return os.system(cmd)

if __name__ == '__main__':
    pass

