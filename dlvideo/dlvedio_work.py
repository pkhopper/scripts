#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import time as _time, sleep as _sleep
from vavava import util
from config import DLVideoConfig
from miniaxel.miniaxel import MiniAxelWorkShop, DownloadUrl


util.set_default_utf8()
import parsers

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
pexists = os.path.exists
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


class DLVideoWork(DownloadUrl):
    def __init__(self, url, out, n=1, proxy=None, bar=False, retrans=False,
                 headers=None, archive_callback=None, timeout=10, log=None):
        DownloadUrl.__init__(self, url, out, n=n, proxy=proxy, bar=bar, retrans=retrans,
                 headers=headers, archive_callback=archive_callback, log=log)

    def dlvideos(self, urls, format, npf, outpath):
        for i, url in enumerate(urls):
            self.dlvideo(url, format, npf, outpath)

    def dlvideo(self, url, format, npf, outpath):
        self.log.info('[DLVideo] START: %s', url)
        parser = parsers.getVidPageParser(url)
        urls, title, ext, nperfile, headers = parser.info(url, vidfmt=format)
        if not ext:
            ext = guess_ext(urls, title)
        title = to_native_string(title)
        self.outname = pjoin(outpath, '%s.%s' % (title, ext))
        self.log.info('[DLVideo] OUT FILE: %s', self.outname)
        if pexists(self.outname):
            self.log.info('[DLVideo] out put file exists, %s', self.outname)
            return

        if nperfile:
            npf = nperfile
        self.tmpdir = pjoin(outpath, escape_file_path(title) + '.downloading')
        self.log.info('[DLVideo] TMP DIR: %s', self.tmpdir)
        util.assure_path(self.tmpdir)

        if not self.axel.isAlive():
            self.axel.start()
        try:
            self.__download(urls, title=title, npf=npf,
                          outpath=outpath, ext=ext, headers=headers)
        except:
            raise
        finally:
            self.axel.setToStop()
            self.axel.join()

    def __download(self, urls, title, npf, outpath, ext=None, headers=None):
        self.clipfiles = []
        self.urlwks = []

        for i, url in enumerate(urls):
            if url.strip().startswith('http'):
                tmpfile = pjoin(self.tmpdir, 'tmp_%d_%d.%s' % (len(urls), i+1, ext))
                if pexists(tmpfile):
                    self.log.info('[DLVideo] clip file exists: %s', tmpfile)
                    continue
                self.clipfiles.append(tmpfile)
                urlwk = DownloadUrl(url, out=tmpfile, headers=headers, n=npf, log=self.log)
                self.urlwks.append(urlwk)

        self.axel.addUrlWorks(self.urlwks)
        count = wknum = len(self.urlwks)
        self.log.debug('[DLVideo] |=> %d files => %s', count, self.outname)

        while count > 0:
            start_at = _time()
            for i, urlwk in enumerate(self.urlwks):
                if urlwk.isArchived():
                    urlwk.cleanUp()
                    count -= 1
                    del self.urlwks[i]
                    self.log.debug('[dlvideo] clip completed (%d/%d): %s', count, wknum, urlwk.out)
                    break
                elif urlwk.isErrorHappen():
                    self.log.error('[dlvideo] urlwork error: %s', urlwk.url)
                    urlwk.cleanUp()
                    curr_urlwk = None
                    raise
            duration = _time() - start_at
            if duration < 1:
                _sleep(1)

        self.__merge(self.clipfiles, self.outname, ext)
        self.cleanUp()

    def __merge(self, files, out, ext):
        if len(files) == 1:
            os.rename(files[0], out)
            return
        if ext == 'flv':
            from flv_join import concat_flvs
            concat = concat_flvs
        elif ext == 'mp4':
            from mp4_join import concat_mp4s
            concat = concat_mp4s
        else:
            self.log.error("[dlvideo] Can't join files: {}".format(files))
            return
        concat(files, out)

    def cleanUp(self):
        for f in self.clipfiles:
            if pexists(f):
                os.remove(f)
        os.removedirs(self.tmpdir)