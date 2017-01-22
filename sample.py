#!/usr/bin/env python3

import xdot
import gi
import json
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
        self.dotwidget.on_click = self.on_click

        self.toggle_edge = False
        self.toggle_delete = False
        self.edge_buffer = None

    def on_click(self, element, event):
        if not self.get_name(element):
            pass

        if self.toggle_edge:
            # We are trying to add a new edge
            if not self.edge_buffer:
                # We have only one node selected
                self.edge_buffer = self.get_name(element)
            else:
                # We need to add a new edge now
                self.get_edge_name(self.get_name(element), self.edge_buffer)

        if self.toggle_delete:
            name = self.get_name(element)
            if type(element) is xdot.ui.elements.Edge:
                self.dotwidget.generator.delete_edge(name)
            if type(element) is xdot.ui.elements.Node:
                self.dotwidget.generator.delete_node(name)

        # Reload graph after each click
        self.dotwidget.load_graph()

    def reset_actions(self):
        self.toggle_edge = False
        self.toggle_delete = False
        self.toggle_start = False
        self.toggle_end = False
        self.edge_buffer = None
        self.actiongroup.get_action('Add Edge').set_active(False)
        self.actiongroup.get_action('Delete').set_active(False)

    def get_name(self, element):
        if not element:
            return None
        name = None
        for shape in element.shapes:
            if type(shape) is xdot.ui.elements.TextShape:
                name = shape.get_text()
        return name

    def save_file(self, filename):
        try:
            with open(filename, 'w') as fp:
                json.dump(self.dotwidget.generator.get_graph(), fp)
        except IOError as ex:
            self.error_dialog(str(ex))

    def on_save(self, action):
        chooser = Gtk.FileChooserDialog(parent=self,
                                        title="Save graph to file",
                                        action=Gtk.FileChooserAction.SAVE,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_SAVE,
                                                 Gtk.ResponseType.OK))
        chooser.set_default_response(Gtk.ResponseType.OK)
        chooser.set_current_folder(self.last_open_dir)
        if chooser.run() == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            print(filename)
            self.save_file(filename)
            chooser.destroy()
        else:
            chooser.destroy()

    def on_open(self, action):
        chooser = Gtk.FileChooserDialog(parent=self,
                                        title="Open json graph file",
                                        action=Gtk.FileChooserAction.OPEN,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        chooser.set_default_response(Gtk.ResponseType.OK)
        chooser.set_current_folder(self.last_open_dir)
        filter = Gtk.FileFilter()
        filter.set_name("JSON graph file")
        filter.add_pattern("*.json")
        chooser.add_filter(filter)
        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        if chooser.run() == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            self.last_open_dir = chooser.get_current_folder()
            chooser.destroy()
            self.open_file(filename)
        else:
            chooser.destroy()

    def open_file(self, filename):
        try:
            fp = open(filename, 'rt')
            self.dotwidget.generator.set_graph(json.loads(fp.read()))
            self.dotwidget.load_graph()
            fp.close()
        except IOError as ex:
            self.error_dialog(str(ex))

    def delete_element(self, action):
        self.toggle_delete = action.get_active()

    def get_edge_name(self, node_from, node_to):
        # Create a dialog window
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.OTHER,
                                message_format="",
                                title="Enter edge name",
                                buttons=Gtk.ButtonsType.OK)

        # Create the actual text input entry
        entry = Gtk.Entry()
        entry.show()

        # Append items to dialog window
        dlg.vbox.pack_end(entry, expand=True, fill=True, padding=0)

        # Grab value once window is closed
        response = dlg.run()
        text = entry.get_text()

        # On continue, destroy it
        dlg.destroy()

        # Create node if all went well
        if response == Gtk.ResponseType.OK and text:
            self.dotwidget.generator.add_edge(node_to, node_from, text)
            self.dotwidget.load_graph()

        self.reset_actions()

    def add_edge(self, action):
        self.toggle_edge = action.get_active()

    def add_node(self, action):
        # Reset all other actions
        self.reset_actions()

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
