#!/usr/bin/env python
# coding=utf-8

import os
import sys
import re
from online_dict import Trans
from vavava import util

from vavava import scriptutils

class EdictConfig(scriptutils.BaseConfig):

    def get_ini_attrs(self):
        return {
            'default  |outpath  |s': None,
        }


    def get_args(self, argv):
        usage = """./edict word"""
        import argparse
        parser=argparse.ArgumentParser(usage=usage, version='0.1')
        parser.add_argument('-c', '--config')
        parser.add_argument('-o', '--outpath',)
        parser.add_argument('-l', '--list',)
        parser.add_argument('words', nargs='*')
        return parser.parse_args()

def wexists(word, dict_string):
    reg = re.compile('^###\s+%s\s+' % (word), re.M|re.I)
    return reg.search(dict_string)

def info(w, dict_string):
    r = re.search("^### (%s(.|\s)+?)^###" % (w), dict_string, re.M|re.I)
    if r:
        return r.group(1)

def main(cfg):
    outfile = os.path.join(cfg.outpath, "edict.md")
    if not os.path.exists(outfile):
        with open(outfile, 'w') as fp:
            dict_string = ''
    else:
        with open(outfile, 'r') as fp:
            dict_string = fp.read()
    with open(outfile, 'a+') as fp:
        for w in cfg.words:
            if wexists(w.strip(), dict_string):
                os.system('say exists')
                print info(w, dict_string)
                continue
            else:
                content = '\n### %s\n%s' % (w, Trans().trans(w))
                print content
                os.system('say %s' % w)
                fp.write(content)

if __name__ == "__main__":
    # from config import EdictConfig
    from sys import argv
    cfg = EdictConfig().read_cmdline_config('edict.ini', __file__, argv)
    cfg.log = util.get_logger()
    # try:
    #     sys.stdout.write('')
    #     for line in sys.stdin:
    #         cfg.words.append(line)
    # except:
    #     pass
    try:
        main(cfg)
    except KeyboardInterrupt:
        print 'stop by user'
        exit(0)
    except Exception as e:
        cfg.log.exception(e)