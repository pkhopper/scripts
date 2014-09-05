#!/usr/bin/env python
# coding=utf-8

import os
import re
from threading import RLock as _RLock
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
    def __init__(self, *t_ip_country):
        self.t, self.ip, self.country = t_ip_country
        self.t = float(self.t)

    def __lt__(self, other):
        return self.t < other.t

    def __str__(self):
        return '{},{},{}'.format(self.t, self.ip, self.country)

class DataFile:
    def __init__(self, host, limit, data_path):
        self.data_path = data_path
        self.hfile = pjoin(data_path, '{}.log'.format(host))
        self.afile = pjoin(data_path, '{}.average.log'.format(host))
        self.limit = limit
        self.hips = None
        self.aips = None
        self.__mutex = _RLock()

    def updateFile(self, ipList):
        util.assure_path(self.data_path)
        with self.__mutex:
            self.hips = self.hList + ipList
            with open(self.hfile, 'w') as fp:
                if len(self.hips) > self.limit:
                    self.hips = self.hips[:self.limit]
                fp.writelines([str(ip) + '\n' for ip in self.hips])
            average = {}
            for ip in self.hips:
                if ip.ip in average:
                    average[ip.ip].append(ip)
                else:
                    average[ip.ip] = [ip]
            self.aips = [IP(sum([t.t for t in v])/len(v), k, v[0].country) for k, v in average.items()]
            with open(self.afile, 'w') as fp:
                fp.writelines([str(ip)+'\n' for ip in self.aips])
        # self.log.info('update %s, new=%d', self.hfile, len(self.ips))

    @property
    def hList(self):
        if not self.hips and os.path.exists(self.hfile):
            with self.__mutex:
                with open(self.hfile, 'r') as fp:
                    self.hips = [IP(*line.strip('\n').split(',')) for line in fp.readlines()]
        return self.hips

    @property
    def aList(self):
        if not self.aips and os.path.exists(self.afile):
            with self.__mutex:
                with open(self.afile, 'r') as fp:
                    self.aips = [IP(*line.strip('\n').split(',')) for line in fp.readlines()]
        return self.aips


class IPScanner(threadutil.ServeThreadBase):
    def __init__(self, log=None):
        threadutil.ServeThreadBase.__init__(self, log=log)
        self.ips = []
        self.info_duration = 3600
        self.host_format = 'http://{}'
        self.dnsservers = ['8.8.8.8', '8.8.4.4']
        self.site_host = 'www.google.com'
        self.data_file = DataFile(self.site_host, 1000, './data')

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
                    print "{},{},{}".format(t, ip, country)
                    if t:
                        self.ips.append(IP(t, ip, country))
        self.log.info('update ips list: end, %d new', len(self.ips))
        return self.ips

    @property
    def ipList(self):
        return self.ips

    def run(self):
        start_at = _time()
        self._set_server_available()
        self.ips = self.resolve_ips()
        self.data_file.updateFile(self.ips)
        while not self.isSetStop():
            if _time() - start_at > self.info_duration:
                self.resolve_ips()
                self.data_file.updateFile(self.ips)
                start_at = _time()
            else:
                _sleep(2)
        self.log.info('IPScanner thread end')


def main():
    scanner = IPScanner(util.get_logger())
    scanner.info_duration = 5
    global coutries_filter
    coutries_filter = {'Singapore'}
    print scanner.data_file.aList
    print scanner.data_file.hList
    scanner.data_file.updateFile([])
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

if __name__ == "__main__":
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