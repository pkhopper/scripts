#!/usr/bin/env python
# coding=utf-8

import os
import re
from datetime import datetime, timedelta
from time import time as _time, sleep as _sleep
from vavava import httputil
from vavava import threadutil
from vavava import util
from proxylib import dnslib_resolve_over_tcp
from ipdb import DatabaseIp, IP
from pac import gfwlist2pac

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath
_now = datetime.now

default_ips ="""
64.233.160.0 - 64.233.191.255
66.102.0.0 - 66.102.15.255
66.249.64.0 - 66.249.95.255
72.14.192.0 - 72.14.255.255
74.125.0.0 - 74.125.255.255
209.85.128.0 - 209.85.255.255
216.239.32.0 - 216.239.63.255
"""

coutries_filter = {
    'Korea', 'Singapore', 'Hong Kong', 'Taiwan', 'Japan',
    'Thailand', 'Russia', 'Indonesia', 'Philippines'
}


def __get_host_ip_local(host='www.google.com', dnsservers=None):
    if not dnsservers:
        dnsservers=['8.8.8.8']
    anwser = dnslib_resolve_over_tcp(host, dnsservers, timeout=1)
    return [ip.rdata for ip in anwser.rr]


def __get_ip_from_github():
    url = r'https://raw.githubusercontent.com/Playkid/Google-IPs/master/README.md'
    http = httputil.HttpUtil()
    html = http.get(url)
    matches = re.split('<th[^>]*>([^<]*)</th>', html)
    countries = dict()
    matches = matches[1:]
    i = 0
    while i < len(matches):
        countries[matches[i]] = re.findall('<td><a[^>]*>([^<]*)</a></td>', matches[i+1])
        i += 2
    return countries


get_host_ip_local = __get_host_ip_local
get_host_ip = __get_ip_from_github
_http = httputil.HttpUtil()


def resolve(host, port=80, host_string='', path=None, timeout=1):
    import socket
    sock = socket.socket(socket.AF_INET)
    sock.settimeout(timeout or None)
    package = 'GET / HTTP/1.1\n'
    if path:
        if not path.startswith('/'):
            path = '/' + path
        package = 'GET %s HTTP/1.1\n' % path
    if host_string:
        package += 'Host: %s\n' % host_string
        package += 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:31.0) Gecko/20100101 Firefox/31.0\n'
        package += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\n'
    package += '\n'
    try:
        start = _time()
        sock.connect((host, port))
        sock.send(package)
        data = sock.recv(1024)
        if not data or len(data) < 1:
            return None
        return _time() - start
    except Exception as e:
        return None
    finally:
        if sock:
            sock.close()


class IPScanner(threadutil.ServeThreadBase):
    def __init__(self, log=None):
        threadutil.ServeThreadBase.__init__(self, log=log)
        self.all_ip = {}
        self.__all_goodip = {}
        self.__all_goodip_list = []

        self.__buff_avg = []
        self.__buff_history = []
        self.__buff_refresh_duration = 5

        self.db_file = './ip.db3'
        self.db = None
        self.info_duration = 3600
        self.host_format = 'http://{}'
        self.dnsservers = ['8.8.8.8', '8.8.4.4']
        self.site_host = 'www.google.com'
        self.pac_cfg = 'pac.cfg'

    def __resolve_all_host_ip(self):
        while True:
            try:
                self.allip = get_host_ip()
                # self.allip['local'] = get_host_ip_local(self.site_host, self.dnsservers)
                break
            except Exception as e:
                self.log.exception(e)
                break
            finally:
                if self.isSetStop():
                    return []

        count1 = count2 = 0
        for country, ips in self.allip.items():
            if country in coutries_filter:
                for ip in ips:
                    if self.isSetStop():
                        break
                    # duration = resolve(self.host_format.format(ip))
                    duration = resolve(ip)
                    print '{}, {}, {}'.format(duration, ip, country)
                    if duration:
                        tmp = IP(duration, ip, country, _now())
                        if ip in self.__all_goodip:
                            count1 += 1
                        else:
                            count2 += 1
                            self.__all_goodip_list.append(tmp)
                        self.__all_goodip[ip] = tmp
                        self.db.insert(duration, ip, country)
        self.log.info('update {}, new {}'.format(count1, count2))

    def __refresh_buffers(self, begin):
        if not begin:
            begin = datetime.now() - timedelta(hours=24)
        self.__buff_avg = self.db.getAvgDurationEachIp(begin=begin)
        self.__buff_history = self.db.getIpRecords(begin=begin)
        self.log.info('update buffers: avg=%d, history=%d',
                      len(self.__buff_avg), len(self.__buff_history))

    @property
    def currBuff(self):
        return self.__all_goodip_list

    @property
    def historyBuff(self):
        return self.__buff_history

    @property
    def avgBuff(self):
        return self.__buff_avg

    def run(self):
        self.db = DatabaseIp(self.db_file)
        self.__refresh_buffers(None)
        self._set_server_available()

        last_resolve_at = 0
        last_refresh_at = 0
        while not self.isSetStop():
            now = _time()
            if now - last_resolve_at > self.info_duration:
                self.__resolve_all_host_ip()
                gfwlist2pac.main(self.pac_cfg)
                last_resolve_at = _time()
            if now - last_refresh_at > self.__buff_refresh_duration:
                self.__refresh_buffers(None)
                last_refresh_at = _time()
            if _time() - now < 1:
                _sleep(2)
        self.log.info('IPScanner thread end')
        if self.db:
            self.db.close()


def main():
    scanner = IPScanner(util.get_logger())
    scanner.info_duration = 5
    global coutries_filter
    coutries_filter = {'Korea'}
    scanner.start()
    _sleep(0.5)
    if scanner.isAvailable():
        print scanner.allip
    try:
        _sleep(1)
        while True:
            _sleep(1)
    except KeyboardInterrupt as e:
        print 'stop by user'
    finally:
        if scanner.isAlive():
            scanner.setToStop()
            scanner.join()


if __name__ == "__main__":
    # main()
    # resolve('127.0.0.1', port=8001, path='curr', timeout=3)
    # resolve('209.20.75.76', timeout=3, host_string='www.sublimetext.com')
    resolve('61.135.169.121', timeout=3)

"""
Saudi Arabia
Korea
Singapore
Egypt
Iceland
Philippines
Indonesia
Serbia
Mauritius
Norway
Netherlands
Slovakia
Kenya
Japan
Taiwan
Iraq
Hong Kong
Russia
Thailand
Bulgaria
"""