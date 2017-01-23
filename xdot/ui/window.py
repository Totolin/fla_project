import gi
import os
import re
import json

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gtk
from .elements import Graph
from .elements import Edge
from .elements import Node
from .elements import TextShape


class FindMenuToolAction(Gtk.Action):
    __gtype_name__ = "FindMenuToolAction"

    def do_create_tool_item(self):
        return Gtk.ToolItem()


new_dotcode = """
    digraph finite_state_machine {
    	rankdir=LR;
    	size="8,5"
    	node [shape = doublecircle]; LR_0 LR_3 LR_4 LR_8;
    	node [shape = circle];
    	LR_0 -> LR_2 [ label = "SS(B)" ];
    	LR_0 -> LR_1 [ label = "SS(S)" ];
    	LR_1 -> LR_3 [ label = "S($end)" ];
    	LR_2 -> LR_6 [ label = "SS(b)" ];
    	LR_2 -> LR_5 [ label = "SS(a)" ];
    	LR_2 -> LR_4 [ label = "S(A)" ];
    	LR_5 -> LR_7 [ label = "S(b)" ];
    	LR_5 -> LR_5 [ label = "S(a)" ];
    	LR_6 -> LR_6 [ label = "S(b)" ];
    	LR_6 -> LR_5 [ label = "S(a)" ];
    	LR_7 -> LR_8 [ label = "S(b)" ];
    	LR_7 -> LR_5 [ label = "S(a)" ];
    	LR_8 -> LR_6 [ label = "S(b)" ];
    	LR_8 -> LR_5 [ label = "S(a)" ];
        LR_10 -> LR_8 [ label = "S(bs)" ];
    }
    """


class DotWindow(Gtk.Window):
    ui = '''
    <ui>
        <toolbar name="ToolBar">
            <toolitem action="Open"/>
            <toolitem action="Save"/>
            <separator/>
            <toolitem action="Add Node"/>
            <toolitem action="Add Edge"/>
            <toolitem action="Delete"/>
            <separator/>
            <toolitem action="Start"/>
            <toolitem action="End"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
            <separator/>
            <toolitem action="Check"/>
            <toolitem name="Find" action="Find"/>
        </toolbar>
    </ui>
    '''

    base_title = 'FLA Project'

    def __init__(self, widget, width=780, height=512):
        Gtk.Window.__init__(self)

        self.graph = Graph()

        window = self

        window.set_title(self.base_title)
        window.set_default_size(width, height)
        vbox = Gtk.VBox()
        window.add(vbox)

        self.dotwidget = widget
        self.dotwidget.connect("error", lambda e, m: self.error_dialog(m))

        # Create a UIManager instance
        uimanager = self.uimanager = Gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup('Actions')
        self.actiongroup = actiongroup

        # Create actions
        actiongroup.add_actions((
            ('Open', Gtk.STOCK_OPEN, None, None, 'Open file', self.on_open),
            ('Check', Gtk.STOCK_HELP, None, None, 'Check DFA', self.on_check_deterministic),
            ('Save', Gtk.STOCK_FLOPPY, None, None, 'Save file', self.on_save),
            ('Add Node', Gtk.STOCK_ADD, None, None, 'Add node', self.add_node),
            ('ZoomIn', Gtk.STOCK_ZOOM_IN, None, None, 'Zoom in', self.dotwidget.on_zoom_in),
            ('ZoomOut', Gtk.STOCK_ZOOM_OUT, None, None, 'Zoom out', self.dotwidget.on_zoom_out),
            ('ZoomFit', Gtk.STOCK_ZOOM_FIT, None, None, 'Zoom fit', self.dotwidget.on_zoom_fit),
            ('Zoom100', Gtk.STOCK_ZOOM_100, None, None, 'Zoom 100', self.dotwidget.on_zoom_100),
        ))

        actiongroup.add_toggle_actions((
            ('Add Edge', Gtk.STOCK_REDO, None, None, 'Add edge', self.add_edge),
            ('Delete', Gtk.STOCK_NO, None, None, 'Delete element', self.delete_element),
            ('Start', Gtk.STOCK_NO, None, None, 'Set node as start', self.set_start),
            ('End', Gtk.STOCK_NO, None, None, 'Set node as final', self.set_final),
        ))

        find_action = FindMenuToolAction("Find", None,
                                         "Check string in DFA", None)
        actiongroup.add_action(find_action)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI descrption
        uimanager.add_ui_from_string(self.ui)

        # Add an info label
        label = Gtk.Label()
        vbox.pack_end(label, False, False, 0)
        self.info_label = label

        # Create a Toolbar
        toolbar = uimanager.get_widget('/ToolBar')
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(self.dotwidget, True, True, 0)

        self.last_open_dir = "."

        self.set_focus(self.dotwidget)

        # Add Find text search
        find_toolitem = uimanager.get_widget('/ToolBar/Find')
        self.textentry = Gtk.Entry(max_length=40)
        self.textentry.set_width_chars(40)
        self.textentry.set_icon_from_stock(0, Gtk.STOCK_FIND)
        find_toolitem.add(self.textentry)

        self.textentry.set_activates_default(True)
        self.textentry.connect("activate", self.textentry_activate, self.textentry)
        self.textentry.connect("changed", self.textentry_changed, self.textentry)

        self.show_all()

        self.dotwidget.on_click = self.on_click
        self.toggle_edge = False
        self.toggle_delete = False
        self.toggle_start = False
        self.toggle_end = False
        self.edge_buffer = None

    def on_click(self, element, event):
        if not self.get_name(element):
            return

        if self.toggle_edge:
            # We are trying to add a new edge
            if not self.edge_buffer:
                # We have only one node selected
                self.edge_buffer = self.get_name(element)
            else:
                # We need to add a new edge now
                self.get_edge_name(self.get_name(element), self.edge_buffer)

            # Reload graph
            self.dotwidget.load_graph()

        if self.toggle_delete:
            if type(element) is Edge:
                node_from = self.get_name(element.get_src())
                node_to = self.get_name(element.get_dst())
                self.dotwidget.generator.delete_edge(node_from, node_to)
            if type(element) is Node:
                name = self.get_name(element)
                self.dotwidget.generator.delete_node(name)

            # Reload graph
            self.dotwidget.load_graph()

        if self.toggle_start:
            if type(element) is Node:
                # Get element name
                name = self.get_name(element)
                self.dotwidget.generator.set_start(name)

                # Reload graph
                self.dotwidget.load_graph()

        if self.toggle_end:
            if type(element) is Node:
                # Get element name
                name = self.get_name(element)
                self.dotwidget.generator.set_final(name)

                # Reload graph
                self.dotwidget.load_graph()

    def reset_actions(self):
        self.toggle_edge = False
        self.toggle_delete = False
        self.toggle_start = False
        self.toggle_end = False
        self.edge_buffer = None
        self.actiongroup.get_action('Add Edge').set_active(False)
        self.actiongroup.get_action('Delete').set_active(False)
        self.actiongroup.get_action('Start').set_active(False)
        self.actiongroup.get_action('End').set_active(False)

    def get_name(self, element):
        if not element:
            return None
        name = None
        for shape in element.shapes:
            if type(shape) is TextShape:
                name = shape.get_text()
        return name

    def save_file(self, filename):
        try:
            with open(filename, 'w') as fp:
                json.dump(self.dotwidget.generator.get_graph(), fp)
        except IOError as ex:
            self.error_dialog(str(ex))

    def on_check_deterministic(self, action):
        if self.dotwidget.generator.is_empty():
            self.info_label.set_text('Automaton is empty!')
            return

        is_deterministic = self.dotwidget.generator.is_deterministic()
        if is_deterministic:
            self.info_label.set_text('Current finite automaton is Deterministic')
        else:
            self.info_label.set_text('Current finite automaton is Non-Deterministic')

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

    def textentry_activate(self, widget, entry):
        # Get text from input (query string)
        text = entry.get_text()

        # Special cases
        if self.dotwidget.generator.is_empty():
            self.info_label.set_text('Automaton is empty!')
            return

        if not self.dotwidget.generator.is_deterministic:
            self.info_label.set_text('Automaton is not deterministic!')
            return

        # Ask generator if query is True
        is_valid = self.dotwidget.generator.check_string(text)

        # Display message
        if is_valid:
            self.info_label.set_text('String is accepted by current DFA!')
        else:
            self.info_label.set_text('String is NOT accepted by current DFA!')

    def set_start(self, action):
        self.toggle_start = action.get_active()

    def set_final(self,action):
        self.toggle_end = action.get_active()

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
                                title="Enter state name",
                                buttons=Gtk.ButtonsType.OK)

        # Create the actual text input entry
        entry = Gtk.Entry()
        entry.show()

        # Create a checkbox
        check = Gtk.CheckButton(label="Final state")
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

    def find_text(self, entry_text):
        found_items = []
        dot_widget = self.dotwidget
        regexp = re.compile(entry_text)
        for element in dot_widget.graph.nodes + dot_widget.graph.edges:
            if element.search_text(regexp):
                found_items.append(element)
        return found_items

    def textentry_changed(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.dotwidget
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)

    def set_filter(self, filter):
        self.dotwidget.set_filter(filter)

    def set_dotcode(self, dotcode, filename=None):
        if self.dotwidget.set_dotcode(dotcode, filename):
            self.update_title(filename)
            self.dotwidget.zoom_to_fit()

    def set_xdotcode(self, xdotcode, filename=None):
        if self.dotwidget.set_xdotcode(xdotcode):
            self.update_title(filename)
            self.dotwidget.zoom_to_fit()

    def update_title(self, filename=None):
        if filename is None:
            self.set_title(self.base_title)
        else:
            self.set_title(os.path.basename(filename) + ' - ' + self.base_title)

    def error_dialog(self, message):
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.ERROR,
                                message_format=message,
                                buttons=Gtk.ButtonsType.OK)
        dlg.set_title(self.base_title)
        dlg.run()
        dlg.destroy()
