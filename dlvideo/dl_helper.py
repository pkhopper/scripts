#!/usr/bin/env python
# coding=utf-8

import threading
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

def _dl_methods(url, filepath, refer):
    # 3 methods to download url
    # 1:
    # Wget().get(url, filepath, referer=refer)
    # 2:
    Axel().get(url, filepath, n=10, referer=refer)
    # 3
    # print 'Downloading %s ...' % filename
    # url_save(url, filepath, bar, refer=refer)
    # bar.done()


def download_urls(urls, title, ext, total_size, output_dir='.', refer=None, merge=True):
    assert urls
    assert ext in ('flv', 'mp4')
    title = to_native_string(title)
    title = escape_file_path(title)
    filename = '%s.%s' % (title, ext)
    filepath = pjoin(output_dir, filename)
    if len(urls) == 1:
        _dl_methods(urls[0], filepath+"!", refer)
        os.rename(filepath+"!", filepath)
    else:
        files = []
        multithread = []
        print 'Downloading %s.%s ...' % (title, ext)
        tmp_path = pjoin(output_dir, '.dlvideo')
        if not os.path.isdir(tmp_path):
            os.mkdir(tmp_path)
        for i, url in enumerate(urls):
            filename = '%s[%02d].%s' % (title, i, ext)
            filepath = pjoin(tmp_path, filename)
            files.append(filepath)
            print "[url] ", url
            multithread.append(DownloadThread(url, filepath, refer))
        for t in multithread:
            t.join()
        if not merge:
            print "not Merge?"
            return
        if ext == 'flv':
            from flv_join import concat_flvs
            concat_flvs(files, pjoin(output_dir, title+'.flv'))
            for f in files:
                os.remove(f)
        elif ext == 'mp4':
            from mp4_join import concat_mp4s
            concat_mp4s(files, pjoin(output_dir, title+'.mp4'))
            for f in files:
                os.remove(f)
        else:
            print "Can't join %s files" % ext
            os.system('say "Can\'t join %s files"' % ext)

def playlist_not_supported(name):
    def f(*args, **kwargs):
        raise NotImplementedError('Play list is not supported for '+name)
    return f

class DownloadThread:
    def __init__(self, url, filepath, refer=None):
        self.url = url
        self.filepath = filepath
        self.refer = refer
        self.thread = threading.Thread(target=self._run)
        self.join = self.thread.join
        self.thread.start()
    def _run(self,*_args, **_kwargs):
        if os.path.isfile(self.filepath):
            print "[Already done, abort] ", self.filepath
            return
        _dl_methods(self.url, self.filepath+"!", self.refer)
        os.rename(self.filepath+"!", self.filepath)

class Wget:
    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 Safari/537.36'
    def get(self, url, out=None, referer=None):
        cmd = "wget -c --user-agent='%s'"%(self.useragent)
        if referer:
            cmd += " --referer='%s'"%(referer)
        if out:
            cmd += " --output-document='%s'"%(out)
        cmd += " '%s'"%(url)
        print cmd
        import os
        os.system(cmd)


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
        os.system(cmd)

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
        os.system(cmd)

if __name__ == '__main__':
    pass

