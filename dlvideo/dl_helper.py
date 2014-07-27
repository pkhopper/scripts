#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
from vavava import httputil


default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

pjoin = os.path.join
dirname = os.path.dirname
abspath = os.path.abspath
exists = os.path.exists


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


def guess_ext(urls, title):
    for url in urls:
        if url.find('mp4') >= 0:
            return 'mp4'
    if title.find('mp4') >= 0:
        return 'mp4'
    return 'flv'


class Downloader:
    def __init__(self, nperfile=5, nthread=1, log=None):
        self.log = log
        if not log:
            self.log = util.get_logger()
        self.nperfile = nperfile
        self.nthread = nthread

    def download(self, urls, title, out_dir, ext=None, headers=None):
        if not ext:
            ext = guess_ext(urls, title)
        title = to_native_string(title)
        file_name = pjoin(out_dir, '%s.%s' % (title, ext))
        tmp_dir = pjoin(out_dir, escape_file_path(title) + '.downloading')
        cfg_file = pjoin(tmp_dir, 'cfg.txt')
        if exists(file_name):
            self.log.info('out put file exists, %s', file_name)
            return
        else:
            util.assure_path(tmp_dir)
            with open(cfg_file, 'w') as fp:
                for url in urls:
                    fp.writelines([url + "\n"])
        tmp_files = []
        self.log.debug('[dl_sequence_start] ===> %s', file_name)
        try:
            for i, url in enumerate(urls):
                if url.strip().startswith('http'):
                    tmp_file = pjoin(tmp_dir, 'tmp_%d_%d.%s' % (len(urls), i, ext))
                    tmp_files.append(tmp_file)
                    self.dl_methods(url, tmp_file, headers=headers)
        except Exception as e:
            raise e
        if len(tmp_files) == 1:
            os.rename(tmp_files[0], file_name)
        else:
            self.merge(tmp_files, file_name, ext)
        os.remove(cfg_file)
        for tmp_file in tmp_files:
            if exists(tmp_file):
                os.remove(tmp_file)
        os.removedirs(tmp_dir)
        self.log.debug('[dl_sequence_end] ===> %s', file_name)

    def dl_methods(self, url, file_name, headers):
        if os.path.exists(file_name):
            self.log.info("file exists, abort: %s", file_name)
            return
        self.log.info('[dl] %s', file_name)
        tmp_file = file_name + '!'
        progress_bar = httputil.ProgressBar()
        self.miniaxel = httputil.MiniAxel(progress_bar=progress_bar, retransmission=True)
        self.miniaxel.dl(url, tmp_file, headers=headers, n=self.nperfile)
        os.rename(tmp_file, file_name)
        self.log.debug('[finish] %s', file_name)

    def merge(self, files, out, ext):
        if len(files) < 2:
            return
        if ext == 'flv':
            from flv_join import concat_flvs
            concat = concat_flvs
        elif ext == 'mp4':
            from mp4_join import concat_mp4s
            concat = concat_mp4s
        else:
            self.log.error("Can't join files: {}".format(files))
            return
        concat(files, out)


class Wget:

    def __init__(self):
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) ' \
                         r'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' \
                         r'33.0.1750.149 Safari/537.36'

    def get(self, url, out=None, headers=None, proxy=None):
        cmd = "wget -c --user-agent='%s'" % (self.useragent)
        if headers:
            for k, v in headers.items():
                if k in ('referer'):
                    cmd += " --referer='%s'" % (v)
                else:
                    cmd += " --header='%s:%s'" % (k, v)
        if out:
            cmd += " --output-document='%s'" % (out)
        if not proxy:
            cmd += " --no-proxy"
        cmd += " '%s'" % (url)
        self.__exec(cmd)

    def __exec(self, cmd):
        print cmd
        self.result = os.system(cmd)
        if self.result != 0:
            raise StandardError("result=%d  %s" % (self.result, cmd))


class Axel:
    def __init__(self):
        self.useragent = r'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) ' \
                         r'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 ' \
                         r'Safari/537.36'

    def get(self, url, out=None, n=None, headers=None):
        cmd = "axel -v -a -U '%s'" % (self.useragent)
        if headers:
            for k, v in headers.items():
                cmd += " -H '%s:%s'" % (k, v)
        if n:
            cmd += " -n %d" % (n)
        if out:
            cmd += " -o '%s'" % (out)
        cmd += " '%s'" % (url)
        self.__exec(cmd)

    def __exec(self, cmd):
        print cmd
        self.result = os.system(cmd)
        if self.result != 0:
            raise StandardError("result=%d  %s" % (self.result, cmd))

if __name__ == '__main__':
    pass