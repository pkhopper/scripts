#!/usr/bin/env python
# coding=utf-8

import os, sys
from vavava.httputil import MiniAxel, ProgressBar
from vavava import util
import config

util.set_default_utf8()
CHARSET = "utf-8"
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

def dl_url(url, fname, cfg, log):
    assert cfg
    if fname is None:
        fname = '%s_%s' % (util.get_time_string(), hash(url))
    tmp_dir = pjoin(cfg.out_dir, '%s.miniaxel' % fname)
    tmp_file = pjoin(tmp_dir, fname)
    target_file = pjoin(cfg.out_dir, fname)
    util.assure_path(tmp_dir)
    try:
        bar = ProgressBar()
        mini = MiniAxel(progress_bar=bar, retrans=cfg.retrans,
                        debug_lvl=cfg.log_level, log=log, proxy=None)
        mini.dl(url, out=tmp_file)
        os.rename(tmp_file, target_file)
        os.rmdir(tmp_dir)
    except:
        raise

def main(argv):
    args, cfg, log = config.init_args_config(argv)
    for url in args.urls:
        log.info('[dl.begin] %s', url)
        dl_url(url, fname=None, cfg=cfg, log=log)
        log.info('[dl.end] %s', url)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
