#!/usr/bin/env python
# coding=utf-8

import os
import sys
import shutil
from vavava import util
util.set_default_utf8()

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
user_path = os.environ['HOME']


default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

def to_native_string(s):
    if type(s) == unicode:
        return s.encode(default_encoding)
    else:
        return s

def escape_file_path(path):
    path = path.replace('/', '-')
    path = path.replace('\\', '-')
    path = path.replace('*', '-')
    path = path.replace('?', '-')
    return path

def dl_methods(url, vfile, refer=None, nthread=10, nperfile=True):
    if os.path.isfile(vfile):
        print "[Already done, abort] ", vfile
        return
    # 3 methods to download url
    tmp_file = vfile + '!'
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
    os.rename(tmp_file, vfile)
    return result


def download_urls(urls, title, ext, odir='.', nthread=10,
                  nperfile=True, refer=None, merge=True):
    assert urls
    assert ext in ('flv', 'mp4')
    title = to_native_string(title)
    title = escape_file_path(title)
    filename = '%s.%s' % (title, ext)
    vfile = pjoin(odir, filename)
    files = []
    print 'Downloading %s.%s ...' % (title, ext)
    tmp_path = pjoin(odir, '.dlvideo')
    if not os.path.isdir(tmp_path):
        os.mkdir(tmp_path)
    for url in urls:
        print "[url] ", url
    print '[============ n=%d ================]'%(len(urls))
    if len(urls) == 1:
        dl_methods(urls[0], vfile=vfile, refer=refer, nthread=10, nperfile=True)
        print 'ok'
        return
    for i, url in enumerate(urls):
        filename = '%s[%02d-%02d].%s' % (title, len(urls), i, ext)
        tmp_file = pjoin(tmp_path, filename)
        files.append(tmp_file)
        print '[dl] %s'%(url)
        dl_methods(url, tmp_file, refer=refer, nthread=10, nperfile=True)
    if not merge:
        print "not Merge?"
        return
    if ext == 'flv':
        from flv_join import concat_flvs
        concat = concat_flvs
    elif ext == 'mp4':
        from mp4_join import concat_mp4s
        concat = concat_mp4s
    else:
        print "Can't join %s files" % ext
        return
    concat(files, pjoin(odir, vfile))
    for f in files:
        os.remove(f)

def playlist_not_supported(name):
    def f(*args, **kwargs):
        raise NotImplementedError('Play list is not supported for '+name)
    return f

# class DownloadThread:
#     def __init__(self, url, file_path, n_perfile=10, refer=None):
#         self.url = url
#         self.file_path = file_path
#         self.n_perfile = n_perfile
#         self.refer = refer
#         self.thread = threading.Thread(target=self._run)
#         self.join = self.thread.join
#         self.thread.start()
#     def _run(self,*_args, **_kwargs):
#         dl_methods(url=self.url, out=self.file_path,
#                     n_perfile=self.n_perfile, refer=self.refer)

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
        if proxy:
            pass
        else:
            cmd += " --no-proxy"
        cmd += " '%s'"%(url)
        print cmd
        import os
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
        import os
        return os.system(cmd)

    def gets(self, urls, out=None, n=None, referer=None):
        cmd = "axel -v -a -U '%s'"%(self.useragent)
        if referer:
            cmd += " -H 'Referer:%s'"%(referer)
        if n:
            cmd += " -n %d"%(n)
        if out:
            cmd += " -o '%s'"%(out)
        for url in urls:
            cmd += " '%s'"%(url)
        print cmd
        import os
        return os.system(cmd)

if __name__ == '__main__':
    pass

