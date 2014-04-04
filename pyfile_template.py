#!/usr/bin/env python
# coding=utf-8

import sys
import getopt



def usage():
    print \
    """
usage:
    cmd [-h] [c configfile]
    """

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
