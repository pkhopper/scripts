#!/usr/bin/env python
# coding=utf-8

import os
import sys
from bencode import bencode
import hashlib
from vavava import util

util.set_default_utf8()
pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


def decode(btfile):
    with open(btfile, 'rb') as fp:
        data = fp.read()
    torrent = bencode.bdecode(data)
    return torrent

def encode(data):
    return bencode.bencode(data)

def decode_file(btfile, infofile='out.txt'):
    with open(infofile, 'w') as fp:
        data = decode(btfile)
        fp.write(str(data))
        return data

def encode_file(infofile='out.txt', btfile=''):
    with open(infofile, 'r') as fp:
        data = eval(fp.read())
    name = data["info"]["name"] + btfile + '.torrent'
    with open(name, 'w') as fp:
        torrent = encode(data)
        fp.write(torrent)

def edit(btfile, data_map):
    data = decode(btfile)
    for k, v in data_map.items():
        data['info'][k] = v
    with open(btfile, 'w') as fp:
        torrent = encode(data)
        fp.write(torrent)
    return data

def usage():
    print 'cmd: decode/encode/edit'
    print '\tbt.py decode btfile [infofile]'
    print '\tbt.py encode infofile [btfile]'
    print '\tbt.py edit btfile info_map'

if __name__ == "__main__":
    log = util.get_logger()
    try:
        cmd = sys.argv[1]
        f1 = sys.argv[2]
        infofile = 'out.json'
        if cmd in ('decode'):
            btfile = f1
            if len(sys.argv) > 3:
                infofile = sys.argv[3]
            data = decode_file(btfile, infofile)
            print data['info']
        elif cmd in ('encode'):
            btfile = ''
            infofile = f1
            if len(sys.argv) > 3:
                btfile = sys.argv[3]
            encode_file(infofile=infofile, btfile=btfile)
        elif cmd in ('edit'):
            btfile = f1
            info_map = eval(sys.argv[3])
            print edit(btfile, info_map)['info']
        elif cmd in ('info'):
            btfile = f1
            print decode(btfile)
        else:
            usage()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
    except Exception as e:
        log.exception(e)

