#!/usr/bin/env python
# coding=utf-8

import os
import json
import re
import zipfile
from sys import argv
from time import localtime, strftime
from vavava import util
util.set_default_utf8()


__all__ = []

def plog(msg):
    print("[*] %s" % msg)

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


def _ignore(top, files, ignores, followlinks):
    for ignore in ignores:
        files = filter(lambda f: ignore not in f[len(top):].split("/"), files)
    return files

def _select(top, files, selects, followlinks):
    fs = []
    for sel in selects:
        fs += filter(lambda f: f.endswith(sel), files)
    return fs


def _create_links_backup_sh(top, links):
    if len(links) == 0:
        return
    fullpath = os.path.join(top, "_recover_links.sh")
    with open(fullpath, "w") as fp:
        fp.writelines(
            [
                "ln -s %s %s\n"%(
                    os.readlink(x).replace(" ", r"\ "), # cmd with space
                    x.replace(" ", r"\ ")
                )
                for x in links
            ]
        )
    return fullpath


def zipit(top, zipfilename, ignores=None, selects=None, followlinks=False):
    join, abspath, basename = os.path.join, os.path.abspath, os.path.basename
    tmp_zip = join(top, zipfilename+"!!")
    shfile = None

    if os.path.isfile(top):
        files = [top]
        top = os.path.dirname(top)
    else:
        files, links = _walk(top, followlinks)
        if ignores:
            files = _ignore(top, files, ignores, followlinks)
        if selects:
            files = _select(top, files, selects, followlinks)
        shfile = _create_links_backup_sh(top, links)
        if shfile:
            files.append(shfile)
    try:
        zf = zipfile.ZipFile(tmp_zip, "w", zipfile.zlib.DEFLATED)
        for name in files:
            zf.write(name, name[len(top):])
        zf.close()
        os.rename(tmp_zip, zipfilename)
        return files
    except Exception as e:
        os.remove(tmp_zip)
        raise e
    finally:
        if shfile:
            os.remove(shfile)


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


def _find_settings_json(dirpath, dir_json):
    if not os.path.exists(dirpath):
        dirpath = os.path.join(dir_json, dirpath)
    if os.path.isdir(dirpath):
        for f in os.listdir(dirpath):
            f = os.path.join(dirpath, f)
            if os.path.isfile(f) and f.endswith('.json'):
                with open(f, 'r') as fp:
                    plog('load %s' % f)
                    return json.load(fp)["settings"]
    elif os.path.isfile(dirpath):
        with open(dirpath, 'r') as fp:
            plog('load %s' % dirpath)
            return json.load(fp)["settings"]

def print_json_fomat(dir_json):
    plog("backup2dp.json not found:")
    plog("eg:")
    with open(os.path.join(dir_json, "backup2dp.json.example"), 'r') as fp:
        print fp.read()

home = os.environ['HOME']
curr_time = lambda: strftime("%Y%m%d%H%M%S", localtime())


def main():
    import getopt
    dir_json = util.script_path(__file__)
    cfg_json = os.path.join(dir_json, 'backup2dp.json')
    debug = None
    opts, args = getopt.getopt(argv[1:], "c:d")
    for k, v in opts:
        if k in ("-c"):
            cfg_json = os.path.abspath(v)
            dir_json = os.path.split(cfg_json)[0]
        elif k in ("-d"):
            debug = True
    if not os.path.exists(cfg_json):
        print_json_fomat(dir_json)
        return
    config = json.load(open(cfg_json))
    outpath = config["outpath"].replace("%(home)", home)
    outpath = os.path.join(outpath, curr_time())
    if debug is None:
        debug = config["debug"] if "debug" in config else False
    for inc in config["includes"]:
        config["settings"] += _find_settings_json(inc, dir_json)
    for setting in config['settings']:
        name = setting['name']
        path = setting['path'].replace("%(home)", home)
        ignores = setting['ignore'] if 'ignore' in setting else None
        selects = setting['selects'] if 'selects' in setting else None
        linkfile = setting['linkfile'] if 'linkfile' in setting else False
        if not os.path.isdir(outpath):
            os.mkdir(outpath)
        out = os.path.join(outpath, name+".zip")
        plog('backuping %s' % path)
        files = zipit(path, out, ignores, selects, linkfile)
        if debug:
            print files
        plog('%d file backuped for %s' % (len(files), path))

def test():
    zipit("/Users/pk/lib", "./test.zip", ["vavava"], False)

if __name__ == "__main__":
    main()
    # test()
    # t1()
    # t1("./")
