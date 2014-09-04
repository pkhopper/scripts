#!/usr/bin/env python
# coding=utf-8

import sys
import json
import StringIO
import BaseHTTPServer
from time import clock as _clock, sleep as _sleep
from SimpleHTTPServer import SimpleHTTPRequestHandler
from ipscanner import IPScanner, IP
from vavava import util

ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"

gIpScanner = None

class MyRequestHandler(SimpleHTTPRequestHandler):
    def _info(self):
        with open(gIpScanner.info_file, 'r') as fp:
            lines = fp.readlines()
            ipmap = dict()
            for line in lines:
                ip, country, t = line.split(',')
                if ip in ipmap:
                    ipmap[ip][1].append(float(t))
                else:
                    ipmap[ip] = (country, [float(t)])
            curr = {}
            for ip in gIpScanner.ipList:
                curr[ip.ip] = float(ip.t)
            avarage = []
            for k, v in ipmap.items():
                avarage.append(IP(k, sum(v[1])/len(v[1]), v[0]))
            result_list = []
            for ip in avarage:
                if ip.ip in curr:
                    result_list.append([ip.t, ip.ip, curr[ip.ip], ip.country])
                else:
                    result_list.append([ip.t, ip.ip, None, ip.country])
        return result_list

    def send_head(self):
        content_type = 'text/html; charset=utf-8'
        req_path = self.path
        pos = req_path.find('?')
        if pos > 0:
            req_path = req_path[:pos]
        if req_path in ('/'):
            self.path = '/www/index.html'
            return SimpleHTTPRequestHandler.send_head(self)
        elif req_path in ('/curr'):
            result_list = [[ip.t, ip.ip, ip.country] for ip in gIpScanner.ipList]
            html = json.dumps({'data': result_list})
        elif req_path in ('/info'):
           html = json.dumps({'data': self._info()})
        else:
            return SimpleHTTPRequestHandler.send_head(self)
        f = StringIO.StringIO(html)
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(f.len))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()
        return f

HandlerClass = MyRequestHandler


def httpserver_serve(log):
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8000
    server_address = ('127.0.0.1', port)

    HandlerClass.protocol_version = Protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    log.info("Serving HTTP on {} port={}".format(sa[0], sa[1]))
    httpd.serve_forever()


if __name__ == "__main__":
    global gIpScanner
    log = util.get_logger(logfile='log.txt')
    gIpScanner = IPScanner(log=log)
    try:
        gIpScanner.start()
        while not gIpScanner.isAvailable():
            _sleep(1)
        httpserver_serve(log)
    except KeyboardInterrupt as e:
        print 'stop by user'
    finally:
        if gIpScanner.isAlive():
            gIpScanner.setToStop()
            gIpScanner.join()
