#!/usr/bin/env python
# coding=utf-8

import sys
import curses
from time import time as _time, sleep as _sleep
from vavava.threadutil import ThreadBase


class Redirector:
    def __init__(self):
        self.buff = ''

    def write(self, b):
        self.buff += b

    def flush(self, *args, **kwargs):
        self.buff = ''

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def writable(self):
        return True

class Interface(ThreadBase):
    def __init__(self):
        ThreadBase.__init__(self)
        self.redirect = False
        self.cleanup_handlers = []

    def add_cleanup_handlers(self, handlers):
        for handler in handlers:
            self.cleanup_handlers.append(handler)

    def serve(self, redirect=False):
        self.redirect = redirect
        ThreadBase.start(self)

    def run_in_curr_thread(self, redirect=False):
        self.redirect = redirect
        self.run()

    def run(self):
        try:
            if self.redirect:
                self.stdout_bak = sys.stdout
                self.stderr_bak = sys.stderr
                self.redirector = Redirector()
                self.redirector.write = self.print_body
                sys.stdout = self.redirector
                sys.stderr = self.redirector
            curses.wrapper(self.__init_and_run)
        except KeyboardInterrupt:
            pass
        except:
            raise
        finally:
            self.cleanup()

    def __init_and_run(self, stdscr):
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
        self.head_win = curses.newwin(1, self.max_x, 0, 0)
        self.body_win = curses.newwin(self.max_y - 1, self.max_x, 1, 0)

        self.__init_head_win()
        self.__init_body_win()
        curses.doupdate()

        self.__run()

    def __run(self):
        while not self.isSetStop():
            c = self.head_win.getch()
            if c == ord('q'):
                return
            print '0--------------0'

    def __init_head_win(self):
        """ Initializes the head/information window """
        x = self.head_win.getyx()[1]
        self.head_win.addstr(0, x, "")
        self.head_win.noutrefresh()

    def __init_body_win(self):
        """ Initializes the body/story window """
        self.body_win.timeout(100)
        self.body_win.keypad(1)
        y, x = self.body_win.getmaxyx()
        self.body_win.noutrefresh()

    def print_head(self, msg):
        self.head_win.clear()
        self.head_win.addstr(0, 0, msg)
        self.head_win.refresh()

    def print_body(self, b):
        y, x = self.body_win.getyx()
        if y >= self.max_y - 1 - 2:
            self.body_win.clear()
        # self.body_win.clear()
        self.body_win.addstr(b)
        self.body_win.refresh()

    def cleanup(self):
        if self.redirector:
            sys.stdout = self.stdout_bak
            sys.stderr = self.stderr_bak
        for handler in self.cleanup_handlers:
            if handler:
                handler(self)


def main():
    interface = Interface()
    interface.serve(redirect=True)

if __name__ == "__main__":
    print '==============='
    main()
    print '==============='
