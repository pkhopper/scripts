#!/usr/bin/env python
# coding=utf-8

__author__ = 'liletian'

import socket
import sys
import os
import time
import getopt
reload (sys).setdefaultencoding ("utf8")

class FileTransfer:
    def __init__(self):
        self.ip = ""
        self.port = 0
        self.fileName = ""
        self.timeout = 30
        self.startAt = 0
        self.sock = None
        self.conn = None
        self.peerAddr = None
        self.dataBuffer = ""

    def serve_once(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind ((self.ip, self.port))
        self.sock.listen (5)
        print "listen at ", self.ip, ":", self.port
        self.conn, self.peerAddr = self.sock.accept ()
        print "connected by ", self.peerAddr
        self.startAt = time.time ()
        self.recv()
        print "recieved data: ", len(self.dataBuffer)
        self.sock.close()

    def recv(self):
        begin = time.time ()
        print 'Connected by ', self.peerAddr, ' at ', begin

        while True:
            # if you got some data, then break after wait sec
            if time.time () - begin > self.timeout:
                break
            try:
                data = self.conn.recv (8192)  # 8192
                if data:
                    self.dataBuffer += data
                    begin = time.time ()
                else:
                    break
                    # time.sleep (0.1)
            except socket.error as e:
                if not e.errno == 11:
                    raise e

    def send(self, ip, port, data):
        self.ip = ip
        self.port = port
        self.sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        err = self.sock.connect_ex((self.ip, self.port))
        print self.sock, "connected ", err
        data_send = 0
        data_send += self.sock.send (data)
        if len (data) == data_send:
            print "send ", len (data)
        else:
            print "err, send ", data_send

        self.sock.close()

def server(ip, port, fileName, force):
    if os.path.exists(fileName):
        print "file exist ", fileName
        if not force:
            return
    s = FileTransfer()

    s.serve_once(ip, port)
    with open(fileName, "wb") as f:
        f.write(s.dataBuffer)
    print "ok "

def client(ip, port, fileName):
    if not os.path.exists (fileName):
        print "file not exist ", fileName
        return
    s = FileTransfer ()
    with open(fileName, "rb") as f:
        while True:
            data = f.read()
            if data:
                s.dataBuffer += data
            else:
                break
    len1 = os.path.getsize(fileName)
    len2 = len(s.dataBuffer)
    assert(len1 == len2)
    s.send(ip, port, s.dataBuffer)
    print len(s.dataBuffer), " sended"

def print_usage(optArray):
    print """
    transfer
    """, optArray

def main():
    global CONFIG
    optArray = [
        "client",
        "server",
        "force",
        "ip=",
        "port=",
        "inputfile=",
        "outputfile=",
    ]
    PARAM = {}
    for cmd in optArray:
        if cmd.endswith ('='):
            PARAM[cmd.replace ('=', '')] = None
        else:
            PARAM[cmd] = False
    check = lambda x: x in PARAM and PARAM[x]

    try:
        opts, args = getopt.getopt (sys.argv[1:], "hic:", optArray)
    except getopt.GetoptError as e:
        print e
        print_usage (optArray)
        return
    if len (opts) == 0:
        print_usage (optArray)
        return
    for opt, arg in opts:
        if arg is not "":
            PARAM[opt.replace ('-', '')] = arg
        else:
            PARAM[opt.replace ('-', '')] = True

    if check ("client"):
        client (PARAM["ip"], int(PARAM["port"]), PARAM["inputfile"])

    if check ("server"):
        server(PARAM["ip"], int(PARAM["port"]), PARAM["outputfile"], PARAM["force"])


if __name__ == "__main__":
    try:
        main ()
    except KeyboardInterrupt as e:
        print 'stop by user'
    exit (0)