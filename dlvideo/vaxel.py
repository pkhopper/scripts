#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import sleep as _sleep
from vavava import util
from vavava.threadutil import TaskBase, WorkShop
from miniaxel.miniaxel import ProgressBar, UrlTask

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


class VUrlTask(TaskBase):
    def __init__(self, url, vidfmt, npf, outpath, bar=None, log=None):
        TaskBase.__init__(self, log=log, callback=None)
        self.url = url
        self.vidfmt = vidfmt
        self.npf = npf
        self.bar = bar
        self.outpath = outpath
        self.targetfiles = []

    def makeSubWorks(self):
        urls, npf, headers = \
            self.parse_url(self.url, self.vidfmt, self.npf, self.outpath)
        if len(urls) == 0:
            self.log.info('[VUrlTask] not a video page, %s', self.url)
            return
        if pexists(self.outname):
            self.log.info('[VUrlTask] out put file exists, %s', self.outname)
            return
        util.assure_path(self.tmpdir)
        self.log.debug('[VUrlTask] OUT FILE: %s', self.outname)
        self.log.debug('[VUrlTask] TMP DIR: %s', self.tmpdir)
        self.__makeSubWorks(urls, headers, npf)
        if len(self.getSubTasks()) == 0:
            self.cleanup()
            return
        for tsk in self.getSubTasks():
            for wk in tsk.makeSubWorks():
                self.subworks.append(wk)
        return self.subworks

    def parse_url(self, url, vidfmt, npf, outpath):
        parser = parsers.getVidPageParser(self.url)
        urls, title, self.ext, nperfile, headers = parser.info(url, vidfmt=vidfmt)
        urls = filter(lambda x: x.strip() != '', urls)
        if not self.ext:
            self.ext = guess_ext(urls, title)
        if nperfile:
            npf = nperfile
        title = to_native_string(title)
        self.outname = pjoin(self.outpath, '%s.%s' % (title, self.ext))
        self.tmpdir = pjoin(self.outpath, escape_file_path(title) + '.downloading')
        return urls, npf, headers

    def __makeSubWorks(self, urls, headers, npf):
        self.targetfiles = []
        self.name_map = dict()
        for i, url in enumerate(urls):
            assert url.strip().startswith('http')
            tmpfile = pjoin(self.tmpdir, 'tmp_%d_%d.downloading.%s' % (len(urls), i+1, self.ext))
            tgtfile = pjoin(self.tmpdir, 'tmp_%d_%d.%s' % (len(urls), i+1, self.ext))
            self.name_map[tmpfile] = tgtfile
            self.targetfiles.append(tgtfile)
            if pexists(tgtfile):
                self.log.debug('[VUrlTask] clip file exists: %s', tmpfile)
                continue
            subtask = UrlTask(url, out=tmpfile, bar=self.bar, retrans=True,
                            headers=headers, npf=npf, log=self.log)
            self.addSubTask(subtask)

    def cleanup(self):
        wknum = len(self.targetfiles)
        if wknum < 1:
            return
        count = wknum - len(self.getSubTasks())
        for i, subtsk in enumerate(self.getSubTasks()):
            subtsk.cleanup()
            if subtsk.isArchived():
                count += 1
                os.rename(subtsk.out, self.name_map[subtsk.out])
                self.log.debug('[VUrlTask] clip complete (%d/%d): %s',
                               count, wknum, subtsk.out)
        if count != wknum:
            self.log.info('[VUrlTask] not complete: %s', self.outname)
            return
        self.__merge()
        for f in self.targetfiles:
            if pexists(f):
                os.remove(f)
        if pexists(self.tmpdir):
            os.removedirs(self.tmpdir)
        self.log.error('[VUrlTask] complete: %s', self.outname)
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
            self.log.error("[VUrlTask] merge failed: {}".format(self.targetfiles))
            return
        concat(self.targetfiles, self.outname)


def main():
    urls = [
        'http://i.youku.com/u/UNTc4NzI3MjY0',
        # 'http://v.youku.com/v_show/id_XNzQ5NDAwMDIw.html?from=y1.1-2.10001-0.1-1',
        'http://v.youku.com/v_show/id_XNzUwMTE2MDQw.html?f=22611771',
        'http://v.youku.com/v_show/id_XNzQ3MjMxMTYw.html'
    ]
    log = util.get_logger()
    bar = ProgressBar()
    ws = WorkShop(tmin=5, tmax=10, log=log)
    dlvs = []
    for i, url in enumerate(urls):
        dlvideo = VUrlTask(url, 0, 3, './tmp', bar=bar, log=log)
        dlvs.append(dlvideo)
    try:
        ws.serve()
        ws.addTasks(dlvs)
        while len(dlvs) > 0:
            for i, dlv in enumerate(dlvs):
                if dlv.isArchived() or dlv.isError():
                    dlvs[i].cleanup()
                    del dlvs[i]
            _sleep(1)
    except Exception as e:
        log.exception(e)
    finally:
        ws.setToStop()
        ws.join()
        print 'ok >>>>>>>>>>>>>>>>>>>>>>>>>'

if __name__ == '__main__':
    main()