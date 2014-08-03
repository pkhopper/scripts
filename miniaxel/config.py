#!/usr/bin/env python
# coding=utf-8

import os
from vavava import scriptutils

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class MiniAxelConfig(scriptutils.BaseConfig):

    def get_ini_attrs(self):
        return {
            'default|out_dir  |s': None,
            'default|retrans  |b': None,
            'default|tmin     |i': None,
            'default|tmax     |i': None,
            'default|nthread  |i': None,
            'proxy  |enable   |b': None,
            'proxy  |addr     |s': None,
            '       |log      | ': scriptutils.get_log_from_config()
        }

    def get_args(self, argv):
        usage = """./mini """
        import argparse
        parser=argparse.ArgumentParser(prog=argv, usage=usage, description='mini axel', version='0.1')
        parser.add_argument('urls', nargs='*')
        parser.add_argument('-c', '--config')
        parser.add_argument('-r', '--retrans', action='store_true')
        parser.add_argument('-o', '--out_dir')
        parser.add_argument('-p', '--proxy', dest='proxy', action='store_true')
        parser.add_argument('-n', '--nthread')
        args = parser.parse_args()
        return args

def miniaxel_test(self):
    from vavava import util
    url = r'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi'
    orig_md5 = r'140c4a7c9735dd3006a877a9acca3c31'
    out_file = r'out_file'
    test_cases = [
        ['mini', '-n', '5', '-r', url],
        ['mini', '-n', '2', '-r', url],
        ['mini', '-n', '1', '-r', url],
        ['mini', '-n', '5', '-r', url],
    ]
    for argv in test_cases:
        try:
            from miniaxel import main as _main
            _main(argv)
            with open(out_file, 'rb') as fp:
                md5 = util.md5_for_file(fp)
            self.assertTrue(orig_md5 == md5)
        except Exception as e:
            print e
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)

if __name__ == '__main__':
    import sys
    cfg = MiniAxelConfig()
    cfg.read_cmdline_config('miniaxel.ini', sys.argv)
    print cfg