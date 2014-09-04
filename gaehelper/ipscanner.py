#!/usr/bin/env python
# coding=utf-8

import os
import Queue
import re
from time import clock as _clock, sleep as _sleep
from vavava import httputil
from vavava import threadutil
from vavava import util
from proxylib import dnslib_resolve_over_tcp

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath

"""
64.233.160.0 - 64.233.191.255
66.102.0.0 - 66.102.15.255
66.249.64.0 - 66.249.95.255
72.14.192.0 - 72.14.255.255
74.125.0.0 - 74.125.255.255
209.85.128.0 - 209.85.255.255
216.239.32.0 - 216.239.63.255
"""

coutries_filter = {
    'Korea', 'Singapore', 'Hong Kong', 'Taiwan', 'Japan', 'Thailand', 'Russia', 'Indonesia', 'Philippines'
}

def local_ips():
    anwser = dnslib_resolve_over_tcp('www.google.com', ['8.8.8.8'], timeout=1)
    return [ip.rdata for ip in anwser.rr]

def get_gips():
    url = r'https://raw.githubusercontent.com/Playkid/Google-IPs/master/README.md'
    http = httputil.HttpUtil()
    # http.add_header('Referer', )
    html = http.get(url)
    matches = re.split('<th[^>]*>([^<]*)</th>', html)
    countries = dict()
    matches = matches[1:]
    i = 0
    while i < len(matches):
        countries[matches[i]] = re.findall('<td><a[^>]*>([^<]*)</a></td>', matches[i+1])
        i += 2
    return countries

def resolve(ip, timeout=1):
    try:
        start = _clock()
        httputil.HttpUtil().get('http://' + ip, timeout=timeout)
        return _clock() - start
    except:
        return None

class IP:
    def __init__(self, ip, t, country=''):
        self.ip = ip
        self.t = t
        self.country = country

    def __lt__(self, other):
        return self.t < other.t

    def __str__(self):
        return '{},{},{}'.format(self.ip, self.country, self.t)


class IPScanner(threadutil.ServeThreadBase):
    def __init__(self, log=None):
        threadutil.ServeThreadBase.__init__(self, log=log)
        self.ip_queue = Queue.PriorityQueue()
        self.ips = []
        self.info_duration = 3600
        self.info_file = 'info.txt'
        self.info_file_limit = 1000

    def _first_round(self):
        while True:
            try:
                self.gips = get_gips()
                self.gips['local'] = local_ips()
                break
            except:
                if self.isSetStop():
                    return []
        for country, ips in self.gips.items():
            if country in coutries_filter:
                for ip in ips:
                    if self.isSetStop():
                        break
                    t = resolve(ip)
                    item = IP(ip, t, country)
                    print str(item)
                    if t:
                        self.ips.append(item)
        return self.ips

    @property
    def ipList(self):
        # self.ips.sort()
        return self.ips

    def run(self):
        start_at = _clock()
        self._set_server_available()
        self.ips = self._first_round()
        self._write_info_file()
        while not self.isSetStop() and self.ips:
            if _clock() - start_at > self.info_duration:
                for ip in self.ips:
                    if self.isSetStop():
                        break
                    t = resolve(ip.ip)
                    if t:
                        ip.t = t
                    else:
                        self.log.warning('failed: resolve({})'.format(ip.ip))
                self._write_info_file()
                start_at = _clock()
            else:
                _sleep(2)

    def _write_info_file(self):
        lines = []
        if os.path.exists(self.info_file):
            with open(self.info_file, 'r') as fp:
                lines = fp.readlines()
        with open(self.info_file, 'w') as fp:
            if len(lines) > self.info_file_limit:
                self.log.info('%s: %d', self.info_file, len(lines))
                lines = lines[:self.info_file_limit]
            fp.writelines(lines)
            fp.writelines([str(ip) + '\n' for ip in self.ips])
            self.log.info('update %s, new=%d', self.info_file, len(self.ips))


if __name__ == "__main__":
    scanner = IPScanner(util.get_logger())
    try:
        scanner.start()
        _sleep(1)
        while True:
            for ip in scanner.ipList:
                print '{} {} {}'.format(ip.ip, ip.t, ip.country)
            _sleep(1)
    except KeyboardInterrupt as e:
        print 'stop by user'
    finally:
        if scanner.isAlive():
            scanner.setToStop()
            scanner.join()


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