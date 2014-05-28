#!/usr/bin/env python
# coding=utf-8

import os
import zipfile
from sys import argv
from time import localtime, strftime

__all__ = []

def walk(top, topdown=True, onerror=None, followlinks=False):
    """
    os.walk() ==> top, dirs, nondirs
    walk() ==> top, dirs, files, dirlinks, filelinks, others
    """
    isfile, islink, join, isdir = os.path.isfile, os.path.islink, os.path.join, os.path.isdir
    try:
        names = os.listdir(top)
    except os.error, os.err:
        if onerror is not None:
            onerror(os.err)
        return

    dirs, files, dlns, flns, others = [], [], [], [], []
    for name in names:
        fullname = join(top, name)
        if isdir(fullname):
            if islink(fullname):
                dlns.append(name)
            else:
                dirs.append(name)
        elif isfile(fullname):
            if islink(fullname):
                flns.append(name)
            else:
                files.append(name)
        else:
            others.append(name)

    if topdown:
        yield top, dirs, files, dlns, flns, others

    for name in dirs:
        for x in walk(join(top, name), topdown, onerror, followlinks):
            yield x

    if followlinks is True:
        for dlink in dlns:
            for x in walk(join(top, dlink), topdown, onerror, followlinks):
                yield x

    if not topdown:
        yield top, dirs, files, dlns, flns, others

__all__.append(walk)


class backupdir:

    @staticmethod
    def _walk(top, followlinks):
        join = os.path.join
        files, links = [], []
        for root, ds, fs, dls, fls, ots in walk(top, followlinks):
            for fn in fs:
                files.append(join(root, fn))
            if followlinks is True:
                for fn in fls:
                    files.append(join(root, fn))

            for fn in dls:
                links.append(join(root, fn))
            for fn in fls:
                links.append(join(root, fn))
        return files, links

    @staticmethod
    def _ignore(top, files, ignores, followlinks):
        for ignore in ignores:
            files = filter(lambda f: ignore not in f[len(top):].split("/"), files)
        return files

    @staticmethod
    def _create_links_backup_sh(top, links):
        if len(links) == 0:
            return
        tmp = os.path.join(top, "_recover_links.sh")
        open(tmp, "w").writelines(
            [
                "ln -s %s %s\n"%(
                    os.readlink(x).replace(" ", r"\ "), # cmd with space
                    x.replace(" ", r"\ ")
                ) 
                for x in links
            ]
        )
        return tmp

    @staticmethod
    def zipit(top, zipfilename, ignores=[], followlinks=False):
        join, abspath, basename = os.path.join, os.path.abspath, os.path.basename
        tmp_zip = join(top, zipfilename+"!!")
        shfile = None

        if os.path.isfile(top):
            files = [top]
            top = os.path.dirname(top)
        else:
            files, links = backupdir._walk(top, followlinks)
            files = backupdir._ignore(top, files, ignores, followlinks)
            shfile = backupdir._create_links_backup_sh(top, links)
            if shfile:
                files.append(shfile)
        try:
            zf = zipfile.ZipFile(tmp_zip, "w", zipfile.zlib.DEFLATED)
            for name in files:
                zf.write(name, name[len(top):])
            zf.close()
            os.rename(tmp_zip, zipfilename)
        except Exception as e:
            os.remove(tmp_zip)
            raise e
        finally:
            if shfile:
                os.remove(shfile)

zipit = backupdir.zipit
__all__.append(zipit)

def unzip_file(zipfilename, unziptodir):
    if not os.path.exists(unziptodir):
        os.mkdir(unziptodir, 0777)
    zfobj = zipfile.ZipFile(zipfilename)
    for name in zfobj.namelist():
        name = name.replace('\\', '/')

        if name.endswith('/'):
            os.mkdir(os.path.join(unziptodir, name))
        else:
            ext_filename = os.path.join(unziptodir, name)
            ext_dir = os.path.dirname(ext_filename)
            if not os.path.exists(ext_dir): os.mkdir(ext_dir, 0777)
            outfile = open(ext_filename, 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

home = os.environ['HOME']
curr_time = lambda: strftime("%Y%m%d%H%M%S", localtime())

def main():
    import getopt
    import json

    cfg_file = __file__[0: __file__.rfind('.')] + r'.json'
    opts, args = getopt.getopt(argv[1:], "c:")
    for k, v in opts:
        if k in ("-c"):
            cfg_file = os.path.abspath(cfg_file)
    config = json.load(open(cfg_file))
    outpath = config["outpath"].replace("%(home)", home)
    outpath = os.path.join(outpath, curr_time())
    for setting in config['settings']:
        name = setting['name']
        path = setting['path'].replace("%(home)", home)
        ignore = setting['ignore']
        linkfile = setting['linkfile']
        print name, path, ignore
        if not os.path.isdir(outpath):
            os.mkdir(outpath)
        out = os.path.join(outpath, name+".zip")
        zipit(path, out, ignore, linkfile)

def test():
    zipit("/Users/pk/lib", "./test.zip", ["vavava"], False)

if __name__ == "__main__":
    main()
    # test()
