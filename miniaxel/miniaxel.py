#!/usr/bin/env python
# coding=utf-8

import os
import sys
from vavava import util
from miniaxel.miniaxel import MiniAxelWorkShop
import config


util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

test_urls = {
        '0d851220f47e7aed4615aebbd5cd2c7a': 'http://localhost/w/dl/test.jpg',
        # '1c9d9fc9b01b4d5d1943b92f23b0e38e': 'http://localhost/w/dl/mysql-connector-java-gpl-5.1.31.msi',
        # '140c4a7c9735dd3006a877a9acca3c31': 'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi',
        # 'asdf': 'http://vavava.baoyibj.com/chaguan/'
}


class ftest:
    def test(self, axel, url, md5, n, log):
        self.url = url
        self.md5 = md5
        self.log = log
        self.n = n
        axel.addUrl(url, out=md5, n=3, archive_callback=self.archive_callback)

    def archive_callback(self, wk):
        if not wk.isArchived():
            self.log.error('[fileTest] wk not archive')
            return
        with open(self.md5, 'rb') as fp:
            ss = util.md5_for_file(fp)
        os.remove(self.md5)
        if self.md5 != ss:
            self.log.error('[fileTest] md5 not match, n={}, {}'.format(self.n, ss))
        else:
            self.log.info('[fileTest] match, n=%d', self.n)
filetest = ftest()

class mtest:
    def test(self, axel, url, md5, n, log):
        self.url = url
        self.md5 = md5
        self.log = log
        self.n = n
        from io import BytesIO
        self.fp = BytesIO()
        axel.addUrl(url, out=self.fp, n=3, archive_callback=self.archive_callback)

    def archive_callback(self, wk):
        if not wk.isArchived():
            self.log.error('[fileTest] wk not archive')
            return
        ss = util.md5_for_file(self.fp)
        self.fp.close()
        del self.fp
        if self.md5 != ss:
            self.log.error('[memTest] md5 not match, n={}, {}'.format(self.n, ss))
        else:
            self.log.info('[memTest] match, n=%d', self.n)
memtest = mtest()


def usage():
    return """
    q --> quit
    t --> tset
    h --> help
    """


def find_name(url):
    u1 = url.split('?')[0]
    if u1.rfind('/') == len(u1) -1:
        u1 = u1[:-1]
    return u1[u1.rfind('/')+1:]


def main(argv):
    cfg = config.MiniAxelConfig()
    cfg.read_cmdline_config('miniaxel.ini', sys.argv)
    log = cfg.log
    axel = MiniAxelWorkShop(tmin=cfg.tmin, tmax=cfg.tmax, bar=True, retrans=True, log=log)
    try:
        axel.start()
        if hasattr(cfg, 'urls'):
            for url in cfg.urls:
                log.info('add %s', url)
                name = pjoin(cfg.out_dir, find_name(url))
                axel.addUrl(url, out=name, n=cfg.nthread)
        while True:
            cmd = raw_input('>>')
            if cmd in ('q'):
                break
            elif cmd in ('h'):
                print usage()
            elif cmd in('test'):
                for md5, url in test_urls.items():
                    filetest.test(axel, url, md5, cfg.nthread, log)
                    # memtest.test(axel, url, md5, cfg.nthread, log)
                    log.debug('add a test work: %s,%s,%d', url, md5, cfg.nthread)
            else:
                url = cmd
                name = pjoin(cfg.out_dir, find_name(url))
                axel.addUrl(url, out=name, n=cfg.nthread)
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        log.exception(e)
        raise
    finally:
        axel.setToStop()
        axel.join()


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
