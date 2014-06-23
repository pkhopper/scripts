#!/usr/bin/env python
# coding=utf-8

import sys
import os
import getopt
import curses
from vavava import util
log = util.get_logger()

class Console:
    def __init__(self):
        self._pre()

    def _pre(self):
        self.stdscr = curses.initscr()
        # curses.noecho()
        curses.cbreak()  # cbreak mode, real time input display
        self.stdscr.keypad(1) # keypad mode, react navigation keys eg:home, page up/down
        self.maxy, self.maxx = self.stdscr.getmaxyx()

    def print_line(self, str, x, y):

        try:
            length = len(str)
            col = self.maxx - x
            row = 1
            if length > col:
                row = length/col
                if length%col > 0:
                    row += 1
            # print '%d,%d,%d,%d,%d,%d,'%(x, y, w, h, self.maxx, self.maxy)
            # raw_input()
            log.info('%d,%d,%d,%d,%d,%d,'%(x, y, row, col, self.maxx, self.maxy))
            pad = curses.newpad(row, col)
            pad.border(1)
            pad.addstr(str)
            pad.refresh(0, 0, 0, 0, row, col)
        except curses.error as e:
            log.exception(e)

    def __del__(self):
        if self.stdscr:
            print 'Console.__del__'
            # terminating curses app sequence.
            curses.nocbreak()
            self.stdscr.keypad(0)
            curses.echo()
            # restore the terminal back to original op
            curses.endwin()

def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """
def test1():
    cls = Console()
    cls.stdscr.addstr('asdfasdfasdf')
    cls.refresh()
    while True:
        import time
        time.sleep(1)

def test():
    cls = Console()
    str = """12345678901234567890123456789012345678901234567890
    12345678901234567890123456789012345678901234567890
    12345678901234567890123456789012345678901234567890
    12345678901234567890123456789012345678901234567890
    12345678901234567890123456789012345678901234567890
    """
    try:
        cls.print_line(str, 10, 10)
    except Exception as e:
        log.exception(e)
    while True:
        import time
        time.sleep(1)

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
    test1()
