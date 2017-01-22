#!/usr/bin/env python3

import xdot
import gi
from gi.repository import Gtk

gi.require_version('Gtk', '3.0')


class MyDotWidget(xdot.DotWidget):
    def __init__(self):
        xdot.DotWidget.__init__(self)

    def load_graph(self):
        dotcode = self.generator.get_dotcode()
        self.set_dotcode(dotcode)


class MyDotWindow(xdot.DotWindow):
    def __init__(self, widget):
        xdot.DotWindow.__init__(self, widget)
        self.dotwidget.connect('clicked', self.on_url_clicked)
        self.dotwidget.on_click = self.on_click

    def on_click(self, element, event):
        print(element, event)

        for shape in element.shapes:
            print(shape)

    def on_url_clicked(self, url):
        print('asd')
        dialog = Gtk.MessageDialog(
            parent=self,
            buttons=Gtk.ButtonsType.OK,
            message_format="%s clicked" % url)
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.run()
        return True

    def add_edge(self, action):
        print(action)

    def add_node(self, action):
        # Create a dialog window
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.OTHER,
                                message_format="",
                                title="Enter node name",
                                buttons=Gtk.ButtonsType.OK)

        # Create the actual text input entry
        entry = Gtk.Entry()
        entry.show()

        # Create a checkbox
        check = Gtk.CheckButton(label="Double circle")
        check.show()

        # Append items to dialog window
        dlg.vbox.pack_end(entry, expand=True, fill=True, padding=0)
        dlg.vbox.pack_end(check, expand=True, fill=True, padding=0)

        # Grab value once window is closed
        response = dlg.run()
        text = entry.get_text()
        is_double = check.get_active()

        # On continue, destroy it
        dlg.destroy()

        # Create node if all went well
        if response == Gtk.ResponseType.OK and text:
            self.dotwidget.generator.add_node(text, is_double)
            self.dotwidget.load_graph()


def main():
    widget = MyDotWidget()
    window = MyDotWindow(widget)
    window.dotwidget.load_graph()
    window.connect('delete-event', Gtk.main_quit)
    Gtk.main()


if __name__ == '__main__':
    main()
