#encoding=utf-8

import os
import codecs

from vavava import util


util.set_default_utf8()
BUFFERSIZE = 1024*1024
pjoin = os.path.join

def filter(c):
    print 'source charset:', c
    if c.lower() == 'gb2312':
        return 'gbk'
    return c

def convert_file(fin, fout, charset):
        print 'convert ', fin
        oldfile = codecs.open(fin, 'r', charset)
        tmpfile = codecs.open(fout, 'a', 'utf-8')
        while True:
            content = oldfile.read(BUFFERSIZE)
            if not content:
                return
            tmpfile.write(content)

def convert2utf8(fin):
    try:
        tmp = fin + '.tmp'
        content = open(fin).read(1024)
        charset = filter(util.get_charset(content))
        convert_file(fin, tmp, charset)
        os.rename(fin, fin+'.old')
        os.rename(tmp, fin)
    except Exception as e:
        os.rename(fin, fin+'.uncovered')
        print e

def convert_dir(din):
    for top, dirs, files, dlns, flns, others in util.walk_dir(din):
        for f in files:
            convert2utf8(pjoin(din, f))

def convert(fileordir):
    fileordir = os.path.abspath(fileordir)
    if os.path.isfile(fileordir):
        print 'convert file:', fileordir
        convert2utf8(fileordir)
    elif os.path.isdir(fileordir):
        print 'convert dir:', fileordir
        convert_dir(fileordir)
    else:
        print 'input error:', fileordir

if __name__ == '__main__':
    convert('/Users/pk/Downloads/tmp/swresult.txt')
    # convert(sys.argv[1])

