#!/usr/bin/env python
# coding=utf-8

import os

pjoin = os.path.join
pdirname = os.path.dirname
pabspath = os.path.abspath


class UserInterface:
    def __init__(self, working_dir='./'):
        self.urls = []
        self.unfinished_works = []
        self.working_dir = pabspath(working_dir)

    def unfinished(self):
        self.unfinished_works = []
        for f in os.listdir(self.working_dir):
            if os.path.isdir(f):
                if f.endswith('.downloading'):
                    self.unfinished_works.append(f)
        return self.unfinished_works

    def recover_unfinished(self, path):
        url_file = pjoin(path, 'url.txt')
        assert os.path.exists(url_file)
        with open(url_file, 'r') as fp:
            self.urls.append(fp.readline())

    def console(self):
        os.chdir(self.working_dir)
        print '>>> %s', self.working_dir
        print '--------------------------------------------'
        for i, work in enumerate(self.unfinished()):
            print "[%03d] %s" % (i, work)
        print '--------------------------------------------'
        print "work seq or new url"
        uinput = raw_input('===> ')
        if uinput.startswith('http'):
            self.urls = uinput.strip().split(' ')
            print '===> ', len(self.urls)
        elif uinput.isdigit():
            target = self.unfinished_works[int(uinput)]
            print '===> resuming... ', target
            self.recover_unfinished(pjoin(self.working_dir, target))
            print '===> ', self.urls[0]
        else:
            self.urls = []   # quit
        return self.urls

if __name__ == "__main__":
    print UserInterface('/Users/pk/download').console()
    
