#!/usr/bin/env python
# coding=utf-8

import os
import sys
from time import time as _time, sleep as _sleep
from vavava import util
from config import DLVideoConfig
from miniaxel.miniaxel import MiniAxelWorkShop, DownloadUrl, ProgressBar


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

def remove_empty_items(olist):
    newlist = []
    for item in olist:
        if item.strip() != '':
            newlist.append(item)
    return newlist


def dl_u2b(url, cmdline, proxy, titleformat, cache):
    cmd = cmdline
    cmd += r' --proxy "%s"' % proxy
    cmd += r' --o "%s"' % titleformat
    cmd += r' --cache-dir "%s"' % cache
    cmd += r' %s' % url
    print('==> %s', cmd)
    os.system(cmd)


class DLVideo:
    def __init__(self, tmin=5, tmax=8, log=None):
        self.axel = MiniAxelWorkShop(tmin=tmin, tmax=tmax, bar=True, retrans=True, log=log)
        self.progress_bar = ProgressBar()
        self.log = log

    def dlvideos(self, urls, vidfmt, npf, outpath):
        for i, url in enumerate(urls):
            self.dlvideo(url, vidfmt, npf, outpath)

    def dlvideo(self, url, vidfmt, npf, outpath):
        self.log.info('[DLVideo] START: %s', url)
        parser = parsers.getVidPageParser(url)
        urls, title, ext, nperfile, headers = parser.info(url, vidfmt=vidfmt)
        urls = remove_empty_items(urls)
        if not ext:
            ext = guess_ext(urls, title)
        title = to_native_string(title)
        self.outname = pjoin(outpath, '%s.%s' % (title, ext))
        if pexists(self.outname):
            self.log.info('[DLVideo] out put file exists, %s', self.outname)
            return
        self.log.info('[DLVideo] OUT FILE: %s', self.outname)
        if nperfile:
            npf = nperfile
        self.tmpdir = pjoin(outpath, escape_file_path(title) + '.downloading')
        self.log.info('[DLVideo] TMP DIR: %s', self.tmpdir)
        util.assure_path(self.tmpdir)

        self.targetfiles = []
        self.name_map = dict()
        self.urlwks = []
        for i, url in enumerate(urls):
            assert url.strip().startswith('http')
            tmpfile = pjoin(self.tmpdir, 'tmp_%d_%d.downloading.%s' % (len(urls), i+1, ext))
            tgtfile = pjoin(self.tmpdir, 'tmp_%d_%d.%s' % (len(urls), i+1, ext))
            self.name_map[tmpfile] = tgtfile
            self.targetfiles.append(tgtfile)
            if pexists(tgtfile):
                self.log.debug('[DLVideo] clip file exists: %s', tmpfile)
                continue
            urlwk = DownloadUrl(url, out=tmpfile, bar=self.progress_bar, retrans=True,
                                headers=headers, n=npf, log=self.log)
            self.urlwks.append(urlwk)

        if not self.axel.isAlive():
            self.axel.start()
        try:
            self.axel.addUrlWorks(self.urlwks)
            self.__loop()
            self.__merge(self.targetfiles, self.outname, ext)
            for f in self.targetfiles:
                if pexists(f):
                    os.remove(f)
            os.removedirs(self.tmpdir)
            self.log.debug('[DLVideo] complete: %s', self.outname)
        except:
            raise
        finally:
            if self.axel.isAlive():
                self.axel.setToStop()
                self.axel.join()

    def __loop(self):
        count = wknum = len(self.urlwks)
        while count > 0:
            start_at = _time()
            for i, urlwk in enumerate(self.urlwks):
                if urlwk.isArchived():
                    urlwk.cleanUp()
                    count -= 1
                    os.rename(urlwk.out, self.name_map[urlwk.out])
                    self.log.debug('[DLVideo] clip complete (%d/%d): %s', count, wknum, urlwk.out)
                    del self.urlwks[i]
                    break
                elif urlwk.isErrorHappen():
                    self.log.error('[DLVideo] urlwork error: %s', urlwk.url)
                    self._stop_all_urlworks(count, wknum)
                    raise
            duration = _time() - start_at
            if duration < 1:
                _sleep(1)

    def _stop_all_urlworks(self, count, wknum):
            for i, urlwk in enumerate(self.urlwks):
                if urlwk.isArchived():
                    urlwk.cleanUp()
                    os.rename(urlwk.out, self.name_map[urlwk.out])
                    count -= 1
                    self.log.debug('[DLVideo] clip completed (%d/%d): %s', count, wknum, urlwk.out)
                else:
                    urlwk.setStop()
                    urlwk.wait()

    def __merge(self, files, out, ext):
        self.log.debug('[DLVideo] merge files(%d) => %s', len(files), out)
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
            self.log.error("[DLVideo] Can't join files: {}".format(files))
            return
        concat(files, out)


def main(cfg, log):
    if cfg.playlist:
        for url in cfg.urls:
            outpath, cfg.urls = parsers.getPlayListParser(url).info(url)
            cfg.outpath = pjoin(cfg.outpath, outpath)
            util.assure_path(cfg.outpath)
            with open(pjoin(cfg.outpath, 'url.txt'), 'w') as fp:
                fp.writelines([url + "\n\n"])
                for i, clip in enumerate(cfg.urls):
                    fp.writelines(["[%03d] %s\n"%(i, clip)])
    if cfg.interact:
        import interface
        cfg.urls = interface.UserInterface(cfg.outpath).console()
    dlvideo = DLVideo(tmin=cfg.tmin, tmax=cfg.tmax, log=log)
    dlvideo.dlvideos(cfg.urls, cfg.format, cfg.npf, cfg.outpath)

if __name__ == "__main__":
    cfg = DLVideoConfig().read_cmdline_config('dlvideo.ini', __file__, sys.argv)
    log = cfg.log
    try:
        main(cfg, log)
        if util.check_cmd('say'):
            os.system(r'say "download finished!!"')
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        log.exception(e)
        if util.check_cmd('say'):
            os.system(r'say "download failed!!"')
        raise


