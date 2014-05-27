#!/usr/bin/env python
# coding=utf-8

import getopt
import urllib2
import urllib
import re
import sys
import os
import gzip
import StringIO
from vavava import util

util.set_default_utf8()

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
menu_title = None

def get_params(pmenustr=None):
    param = []

    if pmenustr:
        paramstring = pmenustr
    else:
        paramstring = sys.argv[2]

    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def GetHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('<meta http-equiv="[Cc]ontent-[Tt]ype" content="text/html; charset=(.+?)"').findall(httpdata)
    if len(match)<=0:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')
    return httpdata

def Get5ivdoData(url):
    # print '[Get5ivdoData]%s'%url
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', UserAgent)
        response = urllib2.urlopen(req)
        httpdata = response.read()
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        response.close()
        return httpdata
    except:
        pass

def showdata(purl):
    imultesite = ''
    isinglemem=''
    ipara = ''
    # dialog = xbmcgui.Dialog()
    link = Get5ivdoData(purl)
    if not link:
        print '[Error] ', purl
        return
    match0 = re.compile('<head>(.+?)</head>').search(link).group(1)
    if match0.find('multesite') > 0:
        imultesite=re.compile('<multesite>(.+?)</multesite>').findall(match0)[0]
    if match0.find('singlemem') > 0:
        isinglemem=re.compile('<singlemem>(.+?)</singlemem>').findall(match0)[0]
    if imultesite == 'TRUE':
        match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url>(.+?)\n').findall(link)
        listA = []
        listP = []
        for imode, ititle, iurl ,iother in match:
            print '%s@%s\n'%(ititle, iurl)
    else:
        ipara = ''
        if match0.find('matchstr') > 0:
            imatchstr=re.compile('<matchstr>(.+?)</matchstr>').findall(match0)[0]
        if match0.find('mflag') > 0:
            imflag=re.compile('<mflag>(.+?)</mflag>').findall(match0)[0]
        if match0.find('sub') > 0:
            isub=re.compile('<sub>(.+?)</sub>').findall(match0)[0]
        else:
            isub=''
        if match0.find('prefix') > 0:
            iiprefix=re.compile('<prefix>(.+?)</prefix>').findall(match0)[0]
            ipara = ipara + "&prefix="+urllib.quote_plus(iiprefix)
        if match0.find('options') > 0:
            iioptions=re.compile('<options>(.+?)</options>').findall(match0)[0]
            ipara = ipara + "&options="+urllib.quote_plus(iioptions)
        match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url><thumb>(.+?)</thumb>').findall(link)
        for imode, ititle, iurl ,ithumb in match:
            print '%s, %s\n'%(ititle, iurl)

def interact(info_array):
    tmp_i = 0
    for imode, ititle, iurl, ithumb in info_array:
        print '[%d]%s'%(tmp_i, ititle)
        tmp_i += 1
    ipt = int(raw_input('=>'))
    imode, ititle, iurl = info_array[ipt][0], info_array[ipt][1], info_array[ipt][2]
    if imode == 'menu':
        url = os.path.join('http://www.5ivdo.net/', iurl)
        print '# Menu:', url
        showmenu(url, print_all)
    elif imode == 'data':
        showdata(os.path.join('http://www.5ivdo.net/', iurl))

def print_all(info_array):
    for imode, ititle, iurl,ithumb in info_array:
        if imode == 'menu':
            showmenu(os.path.join('http://www.5ivdo.net/', iurl), print_all)
        elif imode == 'data':
            showdata(os.path.join('http://www.5ivdo.net/', iurl))

def print_menu(info_array):
    for imode, ititle, iurl,ithumb in info_array:
        if imode == 'menu' and ititle == menu_title:
            showmenu(os.path.join('http://www.5ivdo.net/', iurl), print_all)

def showmenu(purl, handle):
    link = Get5ivdoData(purl)
    if not link:
        return
    match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url><thumb>(.+?)</thumb>').findall(link)
    handle(match)

def rootList(handle):
    irootfile = None
    link = GetHttpData('http://www.5ivdo.net/index.xml')
    match0 = re.compile('<config>(.+?)</config>', re.DOTALL).search(link)
    match = re.compile('<name>(.+?)</name><value>(.+?)</value>').findall(match0.group(1))
    for iname, ivalue in match:
        if iname == 'rootfile':
            irootfile = ivalue
    showmenu(irootfile, handle)

def usage():
    print \
    """
usage:
    cmd [-hi]
    """

if __name__ == "__main__":
    config = ''
    handle = print_all
    opts, args = getopt.getopt(sys.argv[1:], "hic:t:f:", [])
    for k, v in opts:
        if k in ("-h"):
            usage()
            exit(0)
        elif k in ("-c"):
            config = v
        elif k in ("-i"):
            handle = interact
        elif k in ("-t"):
            handle = print_menu
            menu_title = v

    rootList(handle)
    exit(0)
