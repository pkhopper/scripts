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


class IPScanner(threadutil.ServeThreadBase):
    def __init__(self, log=None):
        threadutil.ServeThreadBase.__init__(self, log=log)
        self.all_ip = {}
        self.__all_goodip = {}
        self.__all_goodip_list = []
        self.__history_buff = []
        self.__hbuff_refresh_duration = 60*5
        self.db_file = './ip.db3'
        self.db = None
        self.info_duration = 3600
        self.host_format = 'http://{}'
        self.dnsservers = ['8.8.8.8', '8.8.4.4']
        self.site_host = 'www.google.com'
        self.pac_cfg = 'pac.cfg'

    def resolve_all_host_ip(self):
        while True:
            try:
                self.allip = get_host_ip()
                self.allip['local'] = get_host_ip_local(self.site_host, self.dnsservers)
                break
            except:
                if self.isSetStop():
                    return []
        count1 = count2 = 0
        for country, ips in self.allip.items():
            if country in coutries_filter:
                for ip in ips:
                    if self.isSetStop():
                        break
                    duration = resolve(self.host_format.format(ip))
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

    @property
    def allAvailableIp(self):
        return self.__all_goodip_list

    @property
    def historyIp(self):
        return self.__history_buff

    def run(self):
        self.db = DatabaseIp(self.db_file)
        self.__history_buff = self.db.getIpRecords(begin=datetime.now() - timedelta(hours=24))
        self._set_server_available()
        self.resolve_all_host_ip()
        self.__history_buff = self.db.getIpRecords(begin=datetime.now() - timedelta(hours=24))
        last_resolve_at = last_refresh_at = _time()
        while not self.isSetStop():
            now = _time()
            if now - last_resolve_at > self.info_duration:
                self.resolve_all_host_ip()
                gfwlist2pac.main(self.pac_cfg)
                last_resolve_at = _time()
            elif now - last_refresh_at > self.__hbuff_refresh_duration:
                begin=datetime.now() - timedelta(seconds=self.__hbuff_refresh_duration)
                self.__history_buff += self.db.getIpRecords(begin=begin)
                last_refresh_at = _time()
            else:
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