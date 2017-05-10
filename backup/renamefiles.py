#!/usr/bin/env python

import sys
import os
import getopt
from shutil import copyfile


try:
    reload(sys).setdefaultencoding("utf8")
except:
    pass

pjoin, pabspath, pbasename = os.path.join, os.path.abspath, os.path.basename



class OptionParser():
    def __init__(self, *args):
        self.OPTS = args
        self.PARAM = {}
        for cmd in self.OPTS:
            if cmd.endswith ('='):
                self.PARAM[cmd.replace ('=', '')] = None
            else:
                self.PARAM[cmd] = False

        try:
            opts, sys.args = getopt.getopt (sys.argv[1:], "hic:", self.OPTS)
        except getopt.GetoptError as e:
            print("options:", self.OPTS)
            return
        if len (opts) == 0:
            print("options:", self.OPTS)
            return
        for opt, arg in opts:
            if arg is not "":
                self.PARAM[opt.replace ('-', '')] = arg
            else:
                self.PARAM[opt.replace ('-', '')] = True

    def check(self, opt):
        return opt in self.PARAM and self.PARAM[opt]

    def __getattr__(self, attr_name):
        if attr_name in  self.PARAM:
            return self.PARAM[attr_name]
        else:
            raise(AttributeError, attr_name)



def main():
    args = OptionParser("path=", "force", "out=")
    root = pabspath(args.path if args.path else "./")
    for parent, dirs, files in os.walk(root):
        path_name = os.path.split(parent)
        path_name = path_name[len(path_name)-1]
        for f in files:
            src = pjoin(parent, f)
            dst = pjoin(parent, "%s_%s" % (path_name, f))
            if not args.force:
                print(src, dst)
            elif args.out:
                copyfile(src, dst)
            else:
                os.rename(src, dst)


if __name__ == "__main__":
    try:
        main ()
    except KeyboardInterrupt as e:
        print("stop by user")
    exit (0)