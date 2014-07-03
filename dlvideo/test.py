#!/usr/bin/env python
# coding=utf-8

import sys
import unittest
import dlvideo
import dl_helper

argparse_cases = [
    ['url1', 'url2', 'url3', 'url4'],
    ['url1', 'url2', 'url3', 'url4'],
    ['url1', 'url2', 'url3', 'url4', '-f', 'super', '-c', 'config_test.ini'],
]
class TestDlvideoCase(unittest.TestCase):
    def testArgparse(self):
        for args in argparse_cases:
            sys.argv = ['cmd'] + args
            result = dlvideo.parse_args()
            print result
            self.assertEqual(result.urls, args[:4])

class TestDl_helper(unittest.TestCase):
    def test_dlhelper(self):
        filename = """a\\b'c/d.test"""
        result = dl_helper.escape_file_path(filename)
        self.assertEqual(result, 'a_b_c_d.test')

def suite():
    suite = unittest.TestSuite()
    # suite.addTest(TestDlvideoCase("testSize"))
    suite.addTest(TestDl_helper())
    return suite

if __name__ == "__main__":
    # unittest.main(defaultTest = 'suite')
    runner = unittest.TextTestRunner()
    runner.run(suite)
