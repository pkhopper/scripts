#!/usr/bin/env python
# coding=utf-8


import argparse
from vavava import scriptutils

class DLVideoConfig(scriptutils.BaseConfig):

    def get_ini_attrs(self):
        return {
            'default|outpath         |s': None,
            'default|vidfmt          |i': None,
            'default|dlmethod        |s': None,
            'default|npf             |i': None,
            'default|tmin            |i': None,
            'default|tmax            |i': None,
            'u2b    |u2b_cmd         |s': None,
            'u2b    |u2b_proxy       |s': None,
            'u2b    |u2b_cache       |s': None,
            'u2b    |u2b_title_format| ': lambda cfg: cfg.get('u2b', 'u2b_title_format', raw=True),
            'u2b    |u2b_create_dir  |s': None,
            '       |flv             | ': self.__flvcd,
            '       |log             | ': scriptutils.get_log_from_config()
        }


    def __flvcd(self, cfg):
        flvcd = {}
        for k,v in cfg.items('flvcd'):
            flvcd[k] = v.lower() == 'true'
        return flvcd


    def get_args(self, argv):
        usage = """./dlvideo [-m][-l][-c config][-o output][-f format] url ..."""
        parser=argparse.ArgumentParser(prog=argv, usage=usage, version='0.1')
        parser.add_argument('urls', nargs='*', help='urls')
        parser.add_argument('-c', '--config')
        parser.add_argument('-o', '--outpath')
        parser.add_argument('-m', '--dlmethod')
        parser.add_argument('-i', '--interact', action='store_true', default=False)
        parser.add_argument('-l', '--playlist', action='store_true', default=False)
        parser.add_argument('-f', '--format', type=int, help='[0,3]',choices=[0, 1, 2, 3])
        result = parser.parse_args()
        return result

if __name__ == "__main__":
    import sys
    cfg = DLVideoConfig()
    cfg.read_cmdline_config('dlvideo.ini', argv=sys.argv)
    print cfg