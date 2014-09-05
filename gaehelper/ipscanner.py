#!/usr/bin/env python
# coding=utf-8

import os
import Queue
import re
from time import time as _time, sleep as _sleep
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

def __get_host_ip_local(host='www.google.com', dnsservers=None):
    if not dnsservers:
        dnsservers=['8.8.8.8']
    anwser = dnslib_resolve_over_tcp(host, dnsservers, timeout=1)
    return [ip.rdata for ip in anwser.rr]


def __get_ip_from_github():
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

get_host_ip_local = __get_host_ip_local
get_host_ip = __get_ip_from_github
_http = httputil.HttpUtil()


def resolve(host, timeout=1):
    try:
        start = _time()
        _http.get(host, timeout=timeout)
        return _time() - start
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
        self.hfile = 'info.txt'
        self.info_file_limit = 1000
        self.host_format = 'http://{}'
        self.dnsservers = ['8.8.8.8', '8.8.4.4']
        self.site_host = 'www.google.com'

    def resolve_ips(self):
        self.log.info('update ips list: begin')
        while True:
            try:
                self.gips = get_host_ip()
                self.gips['local'] = get_host_ip_local(self.site_host, self.dnsservers)
                break
            except:
                if self.isSetStop():
                    return []
        for country, ips in self.gips.items():
            if country in coutries_filter:
                for ip in ips:
                    if self.isSetStop():
                        break
                    t = resolve(self.host_format.format(ip))
                    item = IP(ip, t, country)
                    print str(item)
                    if t:
                        self.ips.append(item)
        self.log.info('update ips list: end, %d new', len(self.ips))
        return self.ips

    @property
    def ipList(self):
        # self.ips.sort()
        return self.ips

    def run(self):
        start_at = _time()
        self._set_server_available()
        self.ips = self.resolve_ips()
        self._write_info_file()
        while not self.isSetStop():
            if _time() - start_at > self.info_duration:
                self.resolve_ips()
                self._write_info_file()
                start_at = _time()
            else:
                _sleep(2)
        self.log.info('IPScanner thread end')

    def _write_info_file(self):
        lines = []
        if os.path.exists(self.hfile):
            with open(self.hfile, 'r') as fp:
                lines = fp.readlines()
        with open(self.hfile, 'w') as fp:
            if len(lines) > self.info_file_limit:
                self.log.info('%s: %d', self.hfile, len(lines))
                lines = lines[:self.info_file_limit]
            avarage = {}
            for line in lines:
                ip, t, c, a = line.split(',')
                if ip in avarage:
                    avarage[ip].append(float(t))
                else:
                    avarage[ip] = [float(t)]
            for ip in self.ips:
                if ip.ip in avarage:
                    avarage[ip.ip].append(float(ip.t))
                else:
                    avarage[ip.ip] = [float(ip.t)]
            for k, v in avarage.items():
                avarage[k] = sum(v)/len(v)
            for i, line in enumerate(lines):
                ip, t, c, a = line.split(',')
                lines[i] = '{},{},{},{}\n'.format(ip, t, c, avarage[ip])
            for ip in self.ips:
                lines.append('{},{},{},{}\n'.format(ip.ip, ip.t, ip.country, avarage[ip.ip]))
            fp.writelines(lines)
        self.log.info('update %s, new=%d', self.hfile, len(self.ips))


def main():
    scanner = IPScanner(util.get_logger())
    scanner.info_duration = 5
    global coutries_filter
    coutries_filter = {'Singapore'}
    try:
        scanner.start()
        _sleep(1)
        while True:
            # for ip in scanner.ipList:
            #     print '{} {} {}'.format(ip.ip, ip.t, ip.country)
            _sleep(1)
    except KeyboardInterrupt as e:
        print 'stop by user'
    finally:
        if scanner.isAlive():
            scanner.setToStop()
            scanner.join()

def kk():
    scanner = IPScanner(util.get_logger())
    scanner._write_info_file()

if __name__ == "__main__":
    # kk()
    main()

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