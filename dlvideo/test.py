#!/usr/bin/env python
# coding=utf-8

import sys
import unittest
import dlvideo
import dl_helper

class TestParsers(unittest.TestCase):
    def test_urls(self):
        import parsers
        urls = [
            'http://tv.sohu.com/20120726/n349115692.shtml',
            # 'http://v.youku.com/v_show/id_XNzM3MTQwMDY4.html?f=22506977&ev=1',
            'http://www.56.com/u52/v_MTE4NjA0MDY1.html',
            'http://www.tudou.com/programs/view/ZAoQTPEqjAo/',
            # 'http://www.iqiyi.com/v_19rrhkqzgo.html'
        ]
        for url in urls:
           print parsers.getVidPageParser(url).info(url)

    def test_playlist(self):
        import parsers
        urls = [
            # 'http://tv.sohu.com/20120726/n349115692.shtml',
            # 'http://v.youku.com/v_show/id_XNDIwNjkzMzky.html',
            'http://v.youku.com/v_show/id_XNzIyOTE1NTUy.html?f=22331872',
        ]
        for url in urls:
           print parsers.getPlayListParser(url).info(url)

class TestDl_helper(unittest.TestCase):
    def test_dlhelper(self):
        filename = """a\\b'c/d.test"""
        result = dl_helper.escape_file_path(filename)
        self.assertEqual(result, 'a_b_c_d.test')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDl_helper())
    suite.addTest(TestParsers())
    return suite

if __name__ == "__main__":
    # unittest.main(defaultTest = 'suite')
    runner = unittest.TextTestRunner()
    runner.run(suite)
