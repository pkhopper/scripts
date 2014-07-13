#!/usr/bin/env python
# coding=utf-8

class VidParserBase:
    def info(self, url, vidfmt):
        """
        return [urls], title, ext, multi-thread
            multi-thread: bool, can download by multithread each url.
        """
        raise NotImplementedError(url)

class PlayListFilterBase:
    def info(self, url):
        raise NotImplementedError(url)
