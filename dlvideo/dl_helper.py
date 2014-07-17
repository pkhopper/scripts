#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util


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

    def download(self, urls, title, out_dir, ext=None, referer=None):
        if not ext:
            ext = guess_ext(urls, title)
        title = to_native_string(title)
        file_name = pjoin(out_dir, '%s.%s' % (title, ext))
        tmp_dir = pjoin(out_dir, escape_file_path(title) + '.downloading')
        cfg_file = pjoin(tmp_dir, 'cfg.txt')
        if exists(file_name):
            self.log.info('out put file exists, %s', file_name)
            return
        if exists(tmp_dir):
            self.log.info('tmp file exists, try resume.')
            # with open(cfg_file, 'r') as fp:
            #     recode_urls = fp.readlines()
            #     for i, url in enumerate(recode_urls):
            #         url = url.replace('\n', '')
            #         if url.find(urls[i]) == 0:
            #             self.log.error('urls not mach:\n%s\n%s', url, urls[i])
            #             return
        else:
            util.assure_path(tmp_dir)
            with open(cfg_file, 'w') as fp:
                fp.writelines(urls)
        tmp_files = []
        self.log.debug('[dl_sequence_start] ===> %s', file_name)
        try:
            for i, url in enumerate(urls):
                if url.strip().startswith('http'):
                    tmp_file = pjoin(tmp_dir, 'tmp_%d_%d.%s' % (len(urls), i, ext))
                    tmp_files.append(tmp_file)
                    self.dl_methods(url, tmp_file, referer=referer)
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

    def dl_methods(self, url, file_name, referer, retry=2):
        if os.path.exists(file_name):
            self.log.debug("download file exists, abort.: %s", file_name)
            return
        self.log.info('[dl] %s', file_name)
        # 3 methods to download url
        tmp_file = file_name + '!'
        result = 0
        while True:
            try:
                if self.nperfile == 1:
                    # 1:
                    result = Wget().get(url=url, out=tmp_file, referer=referer)
                else:
                    # 2:
                    result = Axel().get(url=url, out=tmp_file, n=self.nthread, referer=referer)
                # 3
                # print 'Downloading %s ...' % filename
                # url_save(url, tmp_file, bar, refer=refer)
                # bar.done()
            except:
                pass
            if result == 0:
                os.rename(tmp_file, file_name)
                self.log.debug('[finish] %s', file_name)
                return
            else:
                self.log.error('downloader failed({}) with result={}'.format(retry, result))
                retry -= 1
                if retry == 0:
                    self.log.error('[failed] %s(%s)', tmp_file, file_name)
                    return

    def merge(self, files, file, ext):
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
        concat(files, file)

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




#
# def download_urls(urls, title, ext=None, odir='.', nthread=10,
#                   nperfile=1, refer=None, merge=True):
#     if not ext:
#         ext = guess_ext(urls, title)
#     title = to_native_string(title)
#     origin_title = title
#     title = escape_file_path(title)
#     origin_title = '%s.%s' % (origin_title, ext)
#     filename = '%s.%s' % (title, ext)
#     origin_title = pjoin(odir, origin_title)
#     file_name = pjoin(odir, filename)
#     if os.path.exists(origin_title) or os.path.exists(file_name):
#         log.info('out put file exists, %s', origin_title)
#         return
#     files = []
#     # print 'Downloading %s.%s ...' % (title, ext)
#     tmp_path = pjoin(odir, '.dlvideo')
#     util.assure_path(tmp_path)
#     if len(urls) > 1:
#         for i, url in enumerate(urls):
#             filename = '%s[%02d-%02d].%s' % (title, len(urls), i, ext)
#             tmp_file = pjoin(tmp_path, filename)
#             files.append(tmp_file)
#             print '[dl] %s'%(url)
#             dl_methods(url, tmp_file, refer=refer, nthread=10, nperfile=nperfile)
#         if merge:
#             if ext == 'flv':
#                 from flv_join import concat_flvs
#                 concat = concat_flvs
#             elif ext == 'mp4':
#                 from mp4_join import concat_mp4s
#                 concat = concat_mp4s
#             else:
#                 log.error("Can't join files: {}".format(files))
#                 return
#             concat(files, file_name)
#             for f in files:
#                 os.remove(f)
#     else:
#         dl_methods(urls[0], file_name=file_name, refer=refer, nthread=10, nperfile=nperfile)
#         print 'ok'
#     os.rename(file_name, origin_title)
#     return origin_title
