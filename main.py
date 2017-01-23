#!/usr/bin/env python3

import xdot
import gi
from gi.repository import Gtk

gi.require_version('Gtk', '3.0')


def main():
    widget = xdot.DotWidget()
    window = xdot.DotWindow(widget)
    window.dotwidget.load_graph()
    window.connect('delete-event', Gtk.main_quit)
    Gtk.main()


if __name__ == '__main__':
    main()
