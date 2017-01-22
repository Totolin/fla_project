import gi
import os
import re

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gtk
from .elements import Graph


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
            <toolitem action="Reload"/>
            <toolitem action="Save"/>
            <separator/>
            <toolitem action="Add Node"/>
            <toolitem action="Add Edge"/>
            <toolitem action="Delete"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
            <separator/>
            <toolitem name="Find" action="Find"/>
        </toolbar>
    </ui>
    '''

    base_title = 'FLA Project'

    def __init__(self, widget, width=700, height=512):
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
            ('Open', Gtk.STOCK_OPEN, None, None, None, self.on_open),
            ('Reload', Gtk.STOCK_REFRESH, None, None, None, self.on_reload),
            ('Save', Gtk.STOCK_FLOPPY, None, None, None, self.on_save),
            ('Add Node', Gtk.STOCK_ADD, None, None, None, self.add_node),
            ('ZoomIn', Gtk.STOCK_ZOOM_IN, None, None, None, self.dotwidget.on_zoom_in),
            ('ZoomOut', Gtk.STOCK_ZOOM_OUT, None, None, None, self.dotwidget.on_zoom_out),
            ('ZoomFit', Gtk.STOCK_ZOOM_FIT, None, None, None, self.dotwidget.on_zoom_fit),
            ('Zoom100', Gtk.STOCK_ZOOM_100, None, None, None, self.dotwidget.on_zoom_100),
        ))

        actiongroup.add_toggle_actions((
            ('Add Edge', Gtk.STOCK_REDO, None, None, None, self.add_edge),
            ('Delete', Gtk.STOCK_NO, None, None, None, self.delete_element),
        ))

        find_action = FindMenuToolAction("Find", None,
                                         "Find a node by name", None)
        actiongroup.add_action(find_action)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI descrption
        uimanager.add_ui_from_string(self.ui)

        # Create a Toolbar
        toolbar = uimanager.get_widget('/ToolBar')
        vbox.pack_start(toolbar, False, False, 0)

        vbox.pack_start(self.dotwidget, True, True, 0)

        self.last_open_dir = "."

        self.set_focus(self.dotwidget)

        # Add Find text search
        find_toolitem = uimanager.get_widget('/ToolBar/Find')
        self.textentry = Gtk.Entry(max_length=20)
        self.textentry.set_icon_from_stock(0, Gtk.STOCK_FIND)
        find_toolitem.add(self.textentry)

        self.textentry.set_activates_default(True)
        self.textentry.connect("activate", self.textentry_activate, self.textentry);
        self.textentry.connect("changed", self.textentry_changed, self.textentry);

        self.show_all()

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

    def textentry_activate(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.dotwidget
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)
        if (len(found_items) == 1):
            dot_widget.animate_to(found_items[0].x, found_items[0].y)

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

    def on_reload(self, action):
        self.dotwidget.reload()

    def error_dialog(self, message):
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.ERROR,
                                message_format=message,
                                buttons=Gtk.ButtonsType.OK)
        dlg.set_title(self.base_title)
        dlg.run()
        dlg.destroy()
