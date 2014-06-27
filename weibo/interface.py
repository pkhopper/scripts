#!/usr/bin/env python
# coding=utf-8

import sys
import os
import time
import getopt
import Queue
import curses
from vavava import util
log = util.get_logger()
import weibotop

weibo = weibotop.MyWeibo()

class InterfaceActions:
    def do(self, caller):
        raise NotImplementedError()

class PrintMSG(InterfaceActions):
    def __init__(self, msg):
        self.msg = msg
    def do(self, caller):
        caller._print_msg(1, self.msg, 0, 0)

class MsgQueue:
    def __init__(self):
        self.messages = []
        self.mutex = threading.RLock()
    def put(self, msg):
        self.mutex.acquire()
        self.messages.append(msg)
        self.mutex.release()

    def cur(self, i=None):
        if i:
            self.curr = i
        else:
            return self.curr

class Interface:
    def __init__(self):
        self.action_queue = Queue.Queue()

    def init_and_run(self, stdscr):
        """ called by ncurses.wrapper """
        self.stdscr = stdscr

        try:
            curses.curs_set(0)
        except:
            pass

        try:
            curses.use_default_colors()
            bg = -1
        except:
            bg = curses.COLOR_BLACK

        curses.init_pair(1, curses.COLOR_CYAN, bg)
        curses.init_pair(2, curses.COLOR_WHITE, bg)
        curses.init_pair(3, curses.COLOR_GREEN, bg)
        curses.init_pair(4, curses.COLOR_YELLOW, bg)
        curses.init_pair(5, curses.COLOR_RED, bg)

        self.max_y, self.max_x = stdscr.getmaxyx()

        self.head_win = curses.newwin(2, self.max_x, 0, 0)
        self.body_win = curses.newwin(self.max_y-2, self.max_x, 4, 0)

        self.init_head_win()
        self.init_body_win()
        curses.doupdate()

        self.run()

    def init_head_win(self):
        """ Initializes the head/information window """
        x = self.head_win.getyx()[1]
        self.head_win.addstr(0, x, "")
        self.head_win.noutrefresh()

    def init_body_win(self):
        """ Initializes the body/story window """
        self.body_win.timeout(100)
        self.body_win.keypad(1)
        self.body_max_y, self.body_max_x = self.body_win.getmaxyx()
        wait_msg = "Retrieving data from weibo."
        self.body_win.addstr(self.body_max_y/2, self.body_max_x/2 - len(wait_msg)/2, wait_msg, curses.color_pair(3))
        self.body_win.noutrefresh()

    def print_head(self, msg):
        self.head_win.clear()
        self.head_win.addstr(0, 0, msg)
        self.head_win.refresh()

    def print_msg(self, msg):
        self.action_queue.put(PrintMSG(msg))

    def _print_msg(self, i, msg, x=None, y=None, color=None):
        num_wigth = 4
        if not color:
            color = curses.color_pair(3)
        if not x or not y:
            y, x = curses.getsyx()
        w = self.max_x - x
        h = len(msg)/(w - num_wigth) + 1
        msg_win = curses.newwin(h, w, y, x)
        msg_win.border(1)
        msg_win.addstr(0, 0, msg, curses.color_pair(3))
        # msg_win.noutrefresh()
        msg_win.refresh()

    def run(self):
        curses.noecho()
        self.print_head('[%s] login ....')
        weibo.login()
        self.print_head('[%s]' % weibo.screen_name)
        i = 0
        while True:
            try:
                c = self.body_win.getch()    # getch() has a 100ms timeout
                ret = self.handle_keystroke(c)
                if ret == -1:   return
                if not self.action_queue.empty():
                    self.action_queue.get().do(self)
                    i += 1
                    self.print_head('############ action = %d, len=%d' % (i, self.action_queue.qsize()))
                # else:
                #     self.print_head('############ action = %d, len=%d' % (0, self.action_queue.qsize()))
            except KeyboardInterrupt:
                break

    def handle_keystroke(self, char):
        if char == ord('q'):
            return -1
        elif char == ord('m'):
            self.print_msg('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
                           'mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
                           'mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
                           'mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm'
                           'mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
            return

def usage():
    print \
        """
usage:
    cmd [-h] [c configfile]
    """
import threading
class Testthread():
    def __init__(self, target):
        self.target = target
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
    def run(self):
        try:
            self.target()
        except KeyboardInterrupt:
            return

def test():
    interface = Interface()
    curses.wrapper(interface.init_and_run)

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
    test()
