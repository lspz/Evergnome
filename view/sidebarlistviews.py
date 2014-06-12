from gi.repository import Gtk
from consts import NO_FILTER_SELECTION_ID
import gtkutils

class BaseSidebarListView(Gtk.Box):
  
  _events = None
  _source_dict = None # dict
  _header_label = ''
  _no_filter_label = ''
  _change_event_name = ''

  def __init__(self, app):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
    self._events = app.events

    self._combostore = Gtk.ListStore(int, str)  

    self._listview = Gtk.TreeView(self._combostore)
    self._listview.append_column(Gtk.TreeViewColumn('Name', Gtk.CellRendererText(), text=1))
    self._listview.set_grid_lines(Gtk.TreeViewGridLines.NONE)
    self._listview.set_headers_visible(False)
    self._listview.set_enable_search(True)
    self._listview.set_search_column(1)

    selection = self._listview.get_selection()
    selection.set_mode(Gtk.SelectionMode.BROWSE)
    selection.connect('changed', self._on_selection_changed)
    self.pack_start(gtkutils.build_header(self._header_label), False, False, 0)
    self.pack_start(self._listview, True, True, 0)

    # expander = Gtk.Expander()
    # expander.set_label(self._header_label)
    # expander.add(self._listview)
    # expander.get_style_context().add_class('list-header')
    # self.pack_start(expander, True, True, 0)

    #self.set_border_width(5)

  def load_all(self):
    treeiter = self._combostore.append([NO_FILTER_SELECTION_ID, self._no_filter_label])
    for obj in self._source_dict.values():
      self._combostore.append([obj.id, obj.name])
    self._listview.get_selection().select_iter(treeiter)

  def _on_selection_changed(self, selection):
    model, treeiter = selection.get_selected()
    if treeiter != None:
      obj_id = model[treeiter][0]
      self._events.emit(self._change_event_name, obj_id)

class NotebookListView(BaseSidebarListView):
  def __init__(self, app):
    self._source_dict = app.localstore.notebooks # dict
    self._header_label = 'Notebooks'
    self._no_filter_label = 'All Notebooks'
    self._change_event_name = 'notebook_changed'
    BaseSidebarListView.__init__(self, app)

class TagListView(BaseSidebarListView):
  def __init__(self, app):
    self._source_dict = app.localstore.tags # dict
    self._header_label = 'Tags'
    self._no_filter_label = 'All Tags'
    self._change_event_name = 'tag_changed'
    BaseSidebarListView.__init__(self, app)