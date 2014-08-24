#!/usr/bin/env python
# coding=utf-8

from bs4 import BeautifulSoup
from base_types import PlayListFilterBase
from vavava.httputil import HttpUtil


class YoukuPlaylist(PlayListFilterBase):
    def __items(self, html, soup):
        ul = soup.find('ul', attrs={'class': 'items'})
        lis = ul.findAll('li', attrs={'class': 'item'})
        return [li.a['href'] for li in lis]

    def __title(self, html, soup):
        h1 = soup.find("h1", attrs={'class': 'title'})
        title = h1.find('a')
        if title:
            title = title.text
        else:
            title = soup.find('h3', attrs={'class': 'title'})
            title = title.find('a').text
        return title

    def info(self, url):
        if url.find('youku.com') < 0:
            raise ValueError('not a youku.com video url')
        html = HttpUtil().get(url)
        soup = BeautifulSoup(html)
        self.title = self.__title(html, soup)
        self.items = self.__items(html, soup)
        return self.title, self.items

if __name__ == "__main__":
    url = r'http://www.youku.com/show_page/id_zcbfdc4cc962411de83b1.html'
    YoukuPlaylist().info(url)

