#!/usr/bin/env python
# coding=utf-8

import sys
import unittest
import dlvideo

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

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDlvideoCase("testSize"))
    return suite

if __name__ == "__main__":
    # unittest.main(defaultTest = 'suite')
    runner = unittest.TextTestRunner()
    runner.run(suite)
