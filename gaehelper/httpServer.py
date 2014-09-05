#!/usr/bin/env python
# coding=utf-8

import sys
import json
import StringIO
import BaseHTTPServer
from time import sleep as _sleep
from SimpleHTTPServer import SimpleHTTPRequestHandler
from ipscanner import IPScanner, IP
from vavava import util

ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"

gIpScanner = None

class MyRequestHandler(SimpleHTTPRequestHandler):
    def _history(self):
        with open(gIpScanner.hfile, 'r') as fp:
            self.history_lines = fp.readlines()
            ipmap = dict()
            for line in self.history_lines:
                ip, t, country, avarage = line.strip('\n').split(',')
                ipmap[ip] = [avarage, ip, country]
            return [v for k, v in ipmap.items()]

    def _ip_history(self, ip):
        result = []
        if not hasattr(self, 'history_lines'):
            with open(gIpScanner.hfile, 'r') as fp:
                self.history_lines = fp.readlines()
        for line in self.history_lines:
            ip1, t, country, avarage = line.strip('\n').split(',')
            if ip1 == ip:
                result.append(t)
        return [result]

    def send_head(self):
        content_type = 'text/html; charset=utf-8'
        param = ''
        req_path = self.path
        if req_path.find('?') > 0:
            req_path, param = req_path.split('?')
        if req_path in ('/'):
            self.path = '/www/index.html'
            return SimpleHTTPRequestHandler.send_head(self)
        elif req_path in ('/curr'):
            result_list = [[ip.t, ip.ip, ip.country] for ip in gIpScanner.ipList]
            html = json.dumps({'name': 'curr', 'data': result_list, 'columns': ['t', 'ip', 'country']})
        elif req_path in ('/history'):
            html = json.dumps({'name': 'history', 'data': self._history(), 'columns': ['avarage', 'ip', 'country']})
        elif req_path in ('/ip_history'):
            data = self._ip_history(param)
            col = range(len(data[0]))
            html = json.dumps({'name': 'ip_history', 'data': data, 'columns': col})
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
    log = util.get_logger()
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
