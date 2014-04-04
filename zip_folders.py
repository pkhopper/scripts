#!/usr/bin/env python
# coding=utf-8

import sys
import getopt
import shutil
import os
from os.path import join, isdir, abspath

ignore_files = [
    '.zip',
    '.rar'
]

def is_ignore_file(filename, ignores, ignore_sys):
    if ignore_sys and filename.startswith('.'):
        return True
    for ignore in ignores:
        if filename.endswith(ignore):
            return True

def is_ignore_dir(path, ignores, ignore_sys):
    if ignore_sys and path.startswith('.'):
        return True
    for top, dirs, nondirs in os.walk(path):
        for filename in nondirs:
            if ignore_sys and filename.startswith('.'):
                continue
            if not is_ignore_file(filename, ignores, ignore_sys):
                return False
    return True

def log(msg, title=None):
    if title:
        print '[%s] %s'%(title, msg)
    else:
        print msg

def _FIX_osx_special_char(str):
    str = str.strip()
    out = ''
    chars = [' ', '(', ')', '[', ']', '!', '$', '&', '*', ';', '|', '\\']
    for c in str:
        if c in chars:
            out += '\\'
        out += c
    return out
_FIX = _FIX_osx_special_char

def exec_cmd(cmd, *param_list):
    for c in param_list:
        cmd += ' ' + c
    log(cmd)
    os.system(cmd)

def zip_folder(path_src, path_dst, pwd, ignore_sys):
    if not isdir(path_dst):
        os.mkdir(path_dst)
    for item in os.listdir(path_src):
        if ignore_sys and item.startswith('.'):
            log(item, 'ignore')
            continue
        src = join(path_src, item)
        dst = join(path_dst, item)
        if os.path.isdir(src):
            if pwd:
                os.chdir(src)
                exec_cmd('zip', '-r', '-P', _FIX(pwd), _FIX(dst + '.zip'), '*')
            elif is_ignore_dir(src, ignore_files, ignore_sys):
                log(src, 'ignore')
                exec_cmd('cp', '-R', _FIX(src), _FIX(dst))
            else:
                os.chdir(src)
                exec_cmd('zip', '-r', _FIX(dst + '.zip'), '*')
        else:
            if pwd:
                os.chdir(path_src)
                exec_cmd('zip', '-P', _FIX(pwd), _FIX(dst + '.zip'), _FIX(item))
            elif is_ignore_file(src, ignore_files, ignore_sys):
                exec_cmd('cp', _FIX(src), _FIX(dst))
            else:
                os.chdir(path_src)
                exec_cmd('zip', _FIX(dst + '.zip'), _FIX(item))

def usage():
    print \
    """usage:
    zipfolders [-s source] [-d destiny] [-p password]
    """

def main(path_src, path_dst, pwd, ignore_sys_files):
    print 'source dir:', path_src
    print 'destiny dir:', path_dst
    if pwd:
      print 'zip with password'
    path_src = abspath(path_src)
    path_dst = abspath(path_dst)
    if path_dst.startswith(path_src):
        log('dst is in src folder', 'error')
        exit(0)
    zip_folder(path_src, path_dst, pwd, ignore_sys_files)

if __name__ == "__main__":
    pwd = None
    path_src = './'
    path_dst = './zip_folders_out'
    ignore_sys_files = True
    if len(sys.argv) == 1:
        usage()
        exit(0)
    opts, args = getopt.getopt(sys.argv[1:], "p:s:d:h", ["system-files"])
    for k, v in opts:
        if k in ("-h"):
            usage()
            exit(0)
        elif k in ("-s"):
            path_src = v
        elif k in ("-d"):
            path_dst = v
        elif k in ("-p"):
            pwd = v
        elif k in ('--system-files'):
            ignore_sys_files = False

    main(path_src, path_dst, pwd, ignore_sys_files)
