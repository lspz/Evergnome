from gi.repository import Gtk
from consts import SelectionIdConstant

class SidebarView(Gtk.Box):
  def __init__(self, app):
    Gtk.Box.__init__(self)

    self.notebooklistview = NotebookListView(app)
    self.notebooklistview.load_all()
    self.taglistview = TagListView(app)
    self.taglistview.load_all()

    # btn_reveal = Gtk.Button('')
    # btn_reveal.get_style_context().add_class('btn-reveal')
    # btn_reveal.set_relief(Gtk.ReliefStyle.HALF)

    vbox = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    vbox.pack1(self.notebooklistview, resize=True, shrink=False)
    vbox.pack2(self.taglistview, resize=True, shrink=False)

    # paned1 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    # paned1.pack1(self.notelistview, resize=True, shrink=False)
    # paned1.pack2(self.contentbox, resize=True, shrink=False)   

    self.pack_start(vbox, True, True, 0)
    # self.set_margin_left(5)
    # self.set_margin_right(5)

    self.get_style_context().add_class('sidebar')

class BaseSidebarListView(Gtk.Box):
  
  _liststore = None
  _listiters = {}
  _events = None
  _trash_label = 'Trash'
  
  # To be set by subclasses
  _selection_mode = Gtk.SelectionMode.NONE
  _change_event_name = ''
  _source_dict = None 
  _header_label = ''
  _selection_all_label = ''
  _item_icon_name = ''
  _item_all_icon_name = ''

  def __init__(self, app):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
    self._events = app.events

    self._liststore = Gtk.ListStore(int, str, str)  

    cell_renderer_icon = Gtk.CellRendererPixbuf()
    col_icon = Gtk.TreeViewColumn()
    col_icon.pack_start(cell_renderer_icon, False)
    col_icon.add_attribute(cell_renderer_icon, 'icon-name', 2)

    self._listview = Gtk.TreeView(self._liststore)
    self._listview.append_column(col_icon)
    self._listview.append_column(Gtk.TreeViewColumn('Name', Gtk.CellRendererText(), text=1))
    self._listview.set_grid_lines(Gtk.TreeViewGridLines.NONE)
    self._listview.set_headers_visible(False)
    self._listview.set_enable_search(True)
    self._listview.set_search_column(1)
    self._listview.get_style_context().add_class('sidebar-listbox')

    selection = self._listview.get_selection()
    selection.set_mode(self._selection_mode)
    selection.connect('changed', self._on_selection_changed)

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrollbox.add(self._listview)

    self.header = self._build_header(self._header_label)
    self.pack_start(self.header, False, False, 0)
    self.pack_start(scrollbox, True, True, 0)

    # expander = Gtk.Expander()
    # expander.set_label(self._header_label)
    # expander.add(self._listview)
    # expander.get_style_context().add_class('list-header')
    # self.pack_start(expander, True, True, 0)

    #self.set_border_width(5)

  def _build_header(self, label):
    label = Gtk.Label(label, halign=Gtk.Align.START)
    label.get_style_context().add_class('sidebar-header-label')
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
    
    btn_add = Gtk.Button.new_from_icon_name('list-add-symbolic', Gtk.IconSize.MENU)
    btn_add.set_relief(Gtk.ReliefStyle.NONE)
    btn_remove = Gtk.Button.new_from_icon_name('list-remove-symbolic', Gtk.IconSize.MENU)
    btn_remove.set_relief(Gtk.ReliefStyle.NONE)
    btn_edit = Gtk.Button.new_from_icon_name('edit-symbolic', Gtk.IconSize.MENU)
    btn_edit.set_relief(Gtk.ReliefStyle.NONE)

    box.pack_start(label, False, False, 0)
    box.pack_end(btn_edit, False, False, 0)
    box.pack_end(btn_remove, False, False, 0)
    box.pack_end(btn_add, False, False, 0)

    box.get_style_context().add_class('sidebar-header')
    box.set_size_request(180, 20)

    return box

  def load_all(self):
    treeiter = None
    if self._selection_mode != Gtk.SelectionMode.MULTIPLE:
      treeiter = self._liststore.append([SelectionIdConstant.NONE, self._selection_all_label, self._item_all_icon_name])
    for obj in self._source_dict.values():
      self.add_obj(obj)
    if treeiter is not None:
      self._listview.get_selection().select_iter(treeiter)

  def _on_selection_changed(self, selection):
    if self._selection_mode == Gtk.SelectionMode.MULTIPLE:
      treepaths, model = selection.get_selected_rows()
      # huh? iterate selected rows
      # for treepath in treepaths:
      obj_id = treepaths[0][0]
      self._events.emit(self._change_event_name, obj_id)

    else:
      model, treeiter = selection.get_selected()
      if treeiter != None:
        obj_id = model[treeiter][0]
        self._events.emit(self._change_event_name, obj_id)
  
  # Common model interface
  def add_obj(self, obj):
    self._listiters[obj.id] = self._liststore.append([obj.id, obj.name, self._item_icon_name])
  def update_obj(self, obj):
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.set_value(_iter, 1, obj.name)
  def delete_obj(self, obj):
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.remove(_iter)

class NotebookListView(BaseSidebarListView):
  def __init__(self, app):
    # Need to set these before calling super constructor
    self._source_dict = app.localstore.notebooks # dict
    self._selection_mode = Gtk.SelectionMode.BROWSE
    self._change_event_name = 'notebook_changed'
    self._header_label = 'Notebooks'
    self._selection_all_label = 'All Notes'
    self._item_icon_name = 'emblem-documents-symbolic'#'folder-documents-symbolic'
    self._item_all_icon_name = 'emblem-documents-symbolic'

    BaseSidebarListView.__init__(self, app)

  def load_all(self):
    BaseSidebarListView.load_all(self)
    self._liststore.append([SelectionIdConstant.TRASH, self._trash_label, 'user-trash-symbolic'])

class TagListView(BaseSidebarListView):
  def __init__(self, app):
    # Need to set these before calling super constructor
    self._source_dict = app.localstore.tags # dict
    self._selection_mode = Gtk.SelectionMode.MULTIPLE
    self._change_event_name = 'tag_changed'
    self._header_label = 'Tags'
    self._item_icon_name = 'folder-tag'
    self._item_all_icon_name = self._item_icon_name
    # self._selection_all_label = 'All Tags'

    BaseSidebarListView.__init__(self, app)