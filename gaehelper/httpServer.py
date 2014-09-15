#!/usr/bin/env python
# coding=utf-8

import sys
import json
import StringIO
import BaseHTTPServer
from time import sleep as _sleep
from SimpleHTTPServer import SimpleHTTPRequestHandler
from ipscanner import IPScanner
from vavava import util

ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"
log = util.get_logger()
gIpScanner = IPScanner(log=util.get_logger())

class MyRequestHandler(SimpleHTTPRequestHandler):

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
            iplist = [[ip.duration, ip.ip, ip.country, ip.timeString] for ip in gIpScanner.currBuff]
            html = json.dumps({'name': 'curr', 'data': iplist, 'columns': ['duration', 'ip', 'country', 'time']})
        elif req_path in ('/average'):
            history = [[ip.duration, ip.ip, ip.country, ip.timeString] for ip in gIpScanner.avgBuff]
            html = json.dumps({'name': 'history', 'data': history, 'columns': ['average', 'ip', 'country', 'time']})
        elif req_path in ('/ip_history'):
            param = param.strip()
            data = [
                [ip.duration, ip.ip, ip.country, ip.timeString]
                for ip in gIpScanner.historyBuff
                if not param or ip.ip == param
            ]
            html = json.dumps({'name': 'ip_history', 'data': data, 'columns': ['t', 'ip', 'country', 'time']})
        elif req_path in ('/ss'):
            html = json.dumps({'status': gIpScanner.status})
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

    HandlerClass.protocol_version = Protocol
    httpd = ServerClass(('0.0.0.0', port), HandlerClass)

    sa = httpd.socket.getsockname()
    log.info("Serving HTTP on {} port={}".format(sa[0], sa[1]))
    httpd.serve_forever()

if __name__ == "__main__":
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
