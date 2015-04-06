from gi.repository import Gtk, Gio, Gdk
from model.consts import SelectionIdConstant
from model.data_models import Notebook, Tag

class SidebarView(Gtk.Box):
  def __init__(self, app):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

    self.notebooklistview = NotebookListView(app)
    self.notebooklistview.load_all()
    self.taglistview = TagListView(app)
    self.taglistview.load_all()

    self.pack_start(self.notebooklistview, True, True, 0)
    self.pack_start(Gtk.HSeparator(), False, False, 0)
    self.pack_end(self.taglistview, False, False, 0)

    self.get_style_context().add_class('sidebar')


COL_IDX_ID = 0
COL_IDX_NAME = 1
COL_IDX_DISPLAYNAME = 2
COL_IDX_ICONNAME = 3
COL_IDX_EDITABLE = 4

class BaseSidebarListView(Gtk.Box):
  
  _liststore = None
  _listiters = {} # Key: object id, Value: 'iter' for accessing liststore 
  _objects_map = None
  _trash_label = 'Trash'
  
  # Current states
  _name_cell_widget = None

  def __init__(self, objects_map, selection_mode, header_label='', selection_all_label='', item_icon_name='', item_all_icon_name=''):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

    self._selection_mode = selection_mode
    self._objects_map = objects_map 
    self._header_label = header_label
    self._selection_all_label = selection_all_label
    self._item_icon_name = item_icon_name
    self._item_all_icon_name = item_all_icon_name

    # id, name, displayname, icon, editable
    self._liststore = Gtk.ListStore(int, str, str, str, bool)  

    cell_renderer_icon = Gtk.CellRendererPixbuf()
    col_icon = Gtk.TreeViewColumn()
    col_icon.pack_start(cell_renderer_icon, False)
    col_icon.add_attribute(cell_renderer_icon, 'icon-name', COL_IDX_ICONNAME)

    self._name_renderer = Gtk.CellRendererText()
    self._name_renderer.connect('edited', self._on_name_edited)
    self._name_renderer.connect('editing-started', self._on_name_editing_started)
    self._name_column = Gtk.TreeViewColumn('Name', self._name_renderer, text=COL_IDX_DISPLAYNAME, editable=COL_IDX_EDITABLE)

    self._listview = Gtk.TreeView(self._liststore)
    self._listview.append_column(col_icon)
    self._listview.append_column(self._name_column)
    self._listview.set_grid_lines(Gtk.TreeViewGridLines.NONE)
    self._listview.set_headers_visible(False)
    self._listview.set_enable_search(True)
    self._listview.set_search_column(1)
    self._listview.connect('button-press-event', self._on_listview_pressed)
    self._listview.get_style_context().add_class('sidebar-listbox')

    self.selection = self._listview.get_selection()
    self.selection.set_mode(self._selection_mode)
    self.selection.connect('changed', self._on_selection_changed)

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrollbox.set_min_content_height(150)
    scrollbox.add(self._listview)

    self.revealer = Gtk.Revealer()
    self.revealer.add(scrollbox)
    self.revealer.set_reveal_child(True)

    self.header = self._build_header(self._header_label)
    self.pack_start(self.header, False, False, 0)
    self.pack_start(self.revealer, True, True, 0)

    self._build_context_menu()

    # expander = Gtk.Expander()
    # expander.set_label(self._header_label)
    # expander.add(self._listview)
    # expander.get_style_context().add_class('list-header')
    # self.pack_start(expander, True, True, 0)

    #self.set_border_width(5)

  # huh? make this a custom_revealer class that we can use somewhere else
  def _build_header(self, label):
    label = Gtk.Label(label, halign=Gtk.Align.START)
    label.get_style_context().add_class('sub-header-label')
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
    box.get_style_context().add_class('sub-header')
    
    btn_add = Gtk.Button.new_from_icon_name('list-add-symbolic', Gtk.IconSize.MENU)
    btn_add.set_relief(Gtk.ReliefStyle.NONE)
    # btn_remove = Gtk.Button.new_from_icon_name('list-remove-symbolic', Gtk.IconSize.MENU)
    # btn_remove.set_relief(Gtk.ReliefStyle.NONE)
    # btn_edit = Gtk.Button.new_from_icon_name('edit-symbolic', Gtk.IconSize.MENU)
    # btn_edit.set_relief(Gtk.ReliefStyle.NONE)
    # btn_edit.connect('clicked', self._on_edit_pressed)

    self.header_arrow = Gtk.Arrow()
    self.header_arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)

    eventbox = Gtk.EventBox()
    eventbox.add(self.header_arrow)
    eventbox.connect('button-press-event', self._on_arrow_pressed)

    box.pack_start(eventbox, False, False, 0)
    box.pack_start(label, False, False, 0)
    # box.pack_end(btn_edit, False, False, 0)
    # box.pack_end(btn_remove, False, False, 0)
    box.pack_end(btn_add, False, False, 0)

    box.set_size_request(180, 20)

    return box

  def _build_context_menu(self):
    rename_item = Gtk.MenuItem(label='Rename')
    rename_item.connect('activate', self._on_rename_activated)
    self.context_menu = Gtk.Menu()
    self.context_menu.append(rename_item)
    self.context_menu.show_all()
    # self.context_menu = Gio.Menu()
    # self.context_menu.append('Log Out', 'win.logout')

  def load_all(self):
    treeiter = None
    if self._selection_mode != Gtk.SelectionMode.MULTIPLE:
      treeiter = self._liststore.append(
        [SelectionIdConstant.NONE, self._selection_all_label, self._selection_all_label, self._item_all_icon_name, False])
    for obj in self._objects_map.itervalues():
      self.add_obj(obj)
    if treeiter is not None:
      self._listview.get_selection().select_iter(treeiter)
  
  # Common model interface
  def add_obj(self, obj):
    self._listiters[obj.id] = self._liststore.append(
      # id, name, displayname, icon, editable
      [obj.id, obj.name, obj.get_display_name(), self._item_icon_name, False])
    obj.event.connect('updated', self._on_list_obj_updated)
    obj.event.connect('deleted', self._on_list_obj_deleted)

  def _on_listview_pressed(self, widget, event):
    if event.button == Gdk.BUTTON_SECONDARY:
      if self._get_selected_obj_id() not in [SelectionIdConstant.NONE, SelectionIdConstant.TRASH]:
        self.context_menu.popup(None, None, None, None, event.button, event.time)
  
  def _on_selection_changed(self, user_data):
    pass

  def _on_arrow_pressed(self, source, arg):
    self.revealer.set_reveal_child(not self.revealer.get_reveal_child())
    self.header_arrow.set_property('arrow-type', Gtk.ArrowType.DOWN if self.revealer.get_reveal_child() else Gtk.ArrowType.RIGHT)

  # huh? This doesnt work?
  def _on_list_obj_updated(self, event):
    print event
    obj = event.model
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.set_value(_iter, COL_IDX_NAME, obj.name)
      self._liststore.set_value(_iter, COL_IDX_DISPLAYNAME, obj.get_display_name())

  def _on_list_obj_deleted(self, event):
    obj = event.model
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.remove(_iter)

  def _on_rename_activated(self, sender):
    model, treeiter = self.selection.get_selected()
    model[treeiter][COL_IDX_EDITABLE] = True
    self._listview.set_cursor_on_cell(model.get_path(treeiter), self._name_column, self._name_renderer, True)

  def _on_name_edited(self, renderer, path, new_text):
    obj = self._get_selected_obj()
    obj.name = new_text
    obj.save() # This should automatically triggers view update via signal

  def _on_name_editing_started(self, renderer, editable_obj, path):
    print type(editable_obj)
    if type(editable_obj) == Gtk.Entry:
      editable_obj.set_text(self._get_selected_obj_name())

  def _get_selected_obj(self):
    return self._objects_map[self._get_selected_obj_id()]

  def _get_selected_obj_id(self):
    model, treeiter = self.selection.get_selected()
    return model[treeiter][COL_IDX_ID]

  def _get_selected_obj_name(self):
    model, treeiter = self.selection.get_selected()
    return model[treeiter][COL_IDX_NAME]

class NotebookListView(BaseSidebarListView):
  def __init__(self, app):
    BaseSidebarListView.__init__(
      self,
      objects_map = app.localstore.notebooks, 
      selection_mode = Gtk.SelectionMode.BROWSE,
      header_label = 'Notebooks',
      selection_all_label = 'All Notes',
      item_icon_name = 'emblem-documents-symbolic',#'folder-documents-symbolic'
      item_all_icon_name = 'emblem-documents-symbolic')

  def load_all(self):
    BaseSidebarListView.load_all(self)
    self._liststore.append(
      [SelectionIdConstant.TRASH, self._trash_label, self._trash_label, 'user-trash-symbolic', False])

class TagListView(BaseSidebarListView):
  def __init__(self, app):
    BaseSidebarListView.__init__(
      self,
      objects_map = app.localstore.tags, 
      selection_mode = Gtk.SelectionMode.MULTIPLE,
      header_label = 'Tags',
      item_icon_name = 'folder-tag',
      item_all_icon_name = 'folder-tag')
