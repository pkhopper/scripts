#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import sleep as _sleep
from vavava import util
from vavava.threadutil import WorkBase, WorkShop, TaskBase
from miniaxel.miniaxel import ProgressBar, MiniAxelWorkShop, UrlTask


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


def dl_u2b(url, cmdline, proxy, titleformat, cache):
    cmd = cmdline
    cmd += r' --proxy "%s"' % proxy
    cmd += r' --o "%s"' % titleformat
    cmd += r' --cache-dir "%s"' % cache
    cmd += r' %s' % url
    print('==> %s', cmd)
    os.system(cmd)


class DLVWork(WorkBase):
    def __init__(self, url, vidfmt, npf, outpath, axel, id=0, log=None):
        WorkBase.__init__(self, name=id)
        self.vurl = VUrlTask(url, vidfmt, npf, outpath, log)
        self.axel = axel

    def work(self, this_thread, log):
        try:
            wks = self.vurl.makeSubWorks()
            if len(wks) == 0:
                return
            self.axel.addUrlWorks(wks)
            while not self.isSetStop() and not this_thread.isSetStop():
                if self.vurl.isArchived():
                    break
                _sleep(1)
        except Exception as e:
            log.exception(e)
        finally:
            self.vurl.setToStop()
            self.vurl.waitForFinish()
            self.vurl.cleanup()

    def setToStop(self):
        WorkBase.setToStop(self)
        self.vurl.setToStop()


class VUrlTask(TaskBase):
    def __init__(self, url, vidfmt, npf, outpath, log=None):
        TaskBase.__init__(self, log=log, callback=None)
        self.url = url
        self.vidfmt = vidfmt
        self.npf = npf
        self.outpath = outpath
        self.targetfiles = []
        self.urlwks = []

    def makeSubWorks(self):
        return self.makeSubWorks1(url=self.url, vidfmt=self.vidfmt,
                                  npf=self.npf, outpath=self.outpath)

    def makeSubWorks1(self, url, vidfmt, npf, outpath):
        parser = parsers.getVidPageParser(url)
        urls, title, self.ext, nperfile, headers = parser.info(url, vidfmt=vidfmt)
        urls = filter(lambda x: x.strip() != '', urls)
        if len(urls) == 0:
            self.log.info('[DLVideo] not a video page, %s', url)
            return []
        if not self.ext:
            self.ext = guess_ext(urls, title)
        title = to_native_string(title)
        self.outname = pjoin(outpath, '%s.%s' % (title, self.ext))
        if pexists(self.outname):
            self.log.debug('[DLVideo] out put file exists, %s', self.outname)
            return []
        self.log.debug('[DLVideo] OUT FILE: %s', self.outname)
        if nperfile:
            npf = nperfile
        self.tmpdir = pjoin(outpath, escape_file_path(title) + '.downloading')
        self.log.debug('[DLVideo] TMP DIR: %s', self.tmpdir)
        util.assure_path(self.tmpdir)

        self.targetfiles = []
        self.name_map = dict()
        self.urlwks = []
        for i, url in enumerate(urls):
            assert url.strip().startswith('http')
            tmpfile = pjoin(self.tmpdir, 'tmp_%d_%d.downloading.%s' % (len(urls), i+1, self.ext))
            tgtfile = pjoin(self.tmpdir, 'tmp_%d_%d.%s' % (len(urls), i+1, self.ext))
            self.name_map[tmpfile] = tgtfile
            self.targetfiles.append(tgtfile)
            if pexists(tgtfile):
                self.log.debug('[DLVideo] clip file exists: %s', tmpfile)
                continue
            urlwk = UrlTask(url, out=tmpfile, retrans=True, headers=headers, npf=npf, log=self.log)
            self.urlwks.append(urlwk)
        return self.urlwks

    def cleanup(self):
        wknum = len(self.targetfiles)
        count = wknum - len(self.urlwks)
        for i, urlwk in enumerate(self.urlwks):
            urlwk.cleanup()
            if urlwk.isArchived():
                count += 1
                os.rename(urlwk.out, self.name_map[urlwk.out])
                self.log.debug('[DLVideo] clip complete (%d/%d): %s',
                               count, wknum, urlwk.out)
        if count != len(self.urlwks):
            self.log.info('[DLVideo] not complete: %s', self.outname)
        elif count > 0:
            self.__merge()
            for f in self.targetfiles:
                if pexists(f):
                    os.remove(f)
            os.removedirs(self.tmpdir)
            self.log.error('[DLVideo] complete: %s', self.outname)
        TaskBase.cleanup(self)

    def __merge(self):
        if len(self.targetfiles) == 1:
            os.rename(self.targetfiles[0], self.outname)
            return
        if self.ext == 'flv':
            from flv_join import concat_flvs
            concat = concat_flvs
        elif self.ext == 'mp4':
            from mp4_join import concat_mp4s
            concat = concat_mp4s
        else:
            self.log.error("[DLVideo] merge failed: {}".format(self.targetfiles))
            return
        concat(self.targetfiles, self.outname)


class VAxel(WorkShop):
    def __init__(self, axel, log=None):
        WorkShop.__init__(self, tmin=1, tmax=1, log=log)
        self.axel = axel

    def addWork(self, work):
        if isinstance(work, UrlTask):
            self.axel.addUrlWorks([work])
        elif isinstance(work, WorkBase):
            WorkShop.addWork(self, work)
        else:
            raise ValueError('get %s type work, expect WorkBase or DownloadUrl')


def main():
    urls = [
        'http://i.youku.com/u/UNTc4NzI3MjY0',
        # 'http://v.youku.com/v_show/id_XNzQ5NDAwMDIw.html?from=y1.1-2.10001-0.1-1',
        'http://v.youku.com/v_show/id_XNzUwMTE2MDQw.html?f=22611771',
        'http://v.youku.com/v_show/id_XNzQ3MjMxMTYw.html'
    ]
    log = util.get_logger()
    axel = MiniAxelWorkShop(tmin=5, tmax=10, bar=ProgressBar(), retrans=True, log=log)
    vaxel = VAxel(axel=axel, log=log)
    dlvs = []
    for i, url in enumerate(urls):
        dlvideo = DLVWork(url, 0, 3, './tmp', axel, i, log)
        dlvs.append(dlvideo)
    try:
        axel.start()
        vaxel.serve()
        vaxel.addWorks(dlvs)
        cmd = raw_input('>>>>>>')
    except Exception as e:
        log.exception(e)
    finally:
        axel.setToStop()
        axel.join()
        vaxel.setToStop()
        vaxel.join()
        print 'ok >>>>>>>>>>>>>>>>>>>>>>>>>'

if __name__ == '__main__':
    main()