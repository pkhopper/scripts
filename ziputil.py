#!/usr/bin/env python
# coding=utf-8

import sys
import getopt
import zipfile
import os


def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """

def xxxx():
    print "Processing File " + sys.argv[1]
    file=zipfile.ZipFile(sys.argv[1],"r");
    for name in file.namelist():
        utf8name=name.decode('gbk')
        print "Extracting " + utf8name
        pathname = os.path.dirname(utf8name)
        if not os.path.exists(pathname) and pathname!= "":
            os.makedirs(pathname)
        data = file.read(name)
        if not os.path.exists(utf8name):
            fo = open(utf8name, "w")
            fo.write(data)
            fo.close
    file.close()

if __name__ == "__main__":
    config = ''
    opts, args = getopt.getopt(sys.argv[1:], "c:h", ["--long-one"])
    for k, v in opts:
        if k in ("-h"):
            usage()
            exit(0)
        elif k in ("-c"):
            config = v
        elif k in ("--long-one"):
            pass
    else:
        usage()
        exit(0)
