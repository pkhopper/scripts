#!/usr/bin/env python
# coding=utf-8

class VidParserBase:
    def info(self, url, vidfmt):
        raise NotImplementedError(url)

class PlayListFilterBase:
    def info(self, url):
        raise NotImplementedError(url)
