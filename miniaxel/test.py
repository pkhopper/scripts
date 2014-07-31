#!/usr/bin/env python
# coding=utf-8

import sys
import unittest
import os

from vavava import util
import miniaxel

sys.path.insert(0, '.')


__all__ = ['download',]

util.set_default_utf8()


class Test_miniaxel(unittest.TestCase):
    url = r'http://cdn.mysql.com/Downloads/Connector-J/mysql-connector-java-gpl-5.1.31.msi'
    orig_md5 = r'140c4a7c9735dd3006a877a9acca3c31'

    def test_miniaxel(self):
        print 'test_miniaxel'
        out_file = r'out_file'
        test_cases = [
            ['mini', '-n', '5', '-r', Test_miniaxel.url],
            ['mini', '-n', '2', '-r', Test_miniaxel.url],
            ['mini', '-n', '1', '-r', Test_miniaxel.url],
            ['mini', '-n', '5', '-r', Test_miniaxel.url],
        ]
        for argv in test_cases:
            try:
                miniaxel.main(argv)
                with open(out_file, 'rb') as fp:
                    md5 = util.md5_for_file(fp)
                self.assertTrue(Test_miniaxel.orig_md5 == md5)
            except Exception as e:
                print e
            finally:
                if os.path.exists(out_file):
                    os.remove(out_file)


def make_suites():
    test_cases = {
        'mini_axel': 'Test_miniaxel',
    }
    suite = unittest.TestSuite()
    if len(sys.argv) == 1:
        cases = [x for y, x in test_cases.items()]
    else:
        cases = [test_cases[x] for x in sys.argv[1:]]
    mod = sys.modules[__name__]
    for cls_name in cases:
        testcase = getattr(mod, cls_name)
        for attr, obj in testcase.__dict__.items():
            if attr.startswith('test_'):
                suite.addTest(testcase(attr))
    return suite


if __name__ == "__main__":
    try:
        runner = unittest.TextTestRunner()
        runner.run(make_suites())
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        print e
    finally:
        pass