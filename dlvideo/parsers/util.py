#!/usr/bin/env python
# coding=utf-8

import re

def r1(pattern, text, flag=0):
    m = re.search(pattern, text, flag)
    if m:
        return m.group(1)

def r0(pattern, text, flag=0):
    m = re.search(pattern, text, flag)
    if m:
        return m.group(0)

def unescape_html(html):
    import xml.sax.saxutils
    html = xml.sax.saxutils.unescape(html)
    html = re.sub(r'&#(\d+);', lambda x: unichr(int(x.group(1))), html)
    return html

def escape_file_path(path):
    path = path.replace('/', '_')
    path = path.replace('\\', '_')
    path = path.replace('*', '_')
    path = path.replace('?', '_')
    path = path.replace('\'', '_')
    return path
