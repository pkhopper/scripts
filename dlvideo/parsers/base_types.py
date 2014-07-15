#!/usr/bin/env python
# coding=utf-8

class VidParserBase:
    def info(self, url, vidfmt):
        """
        return [urls], title, ext, multi-thread, referer
            multi-thread: bool, can download by multi-thread each url.
        """
        raise NotImplementedError(url)

class PlayListFilterBase:
    def info(self, url):
        raise NotImplementedError(url)
