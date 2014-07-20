from gi.repository import Gtk
from model.consts import SelectionIdConstant
from model.data_models import Notebook, Tag

class SidebarView(Gtk.Box):
  def __init__(self):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

    self.notebooklistview = NotebookListView()
    self.notebooklistview.load_all()
    # self.notebooklistview.set_valign(Gtk.Align.START)
    self.taglistview = TagListView()
    self.taglistview.load_all()

    self.pack_start(self.notebooklistview, True, True, 0)
    self.pack_start(Gtk.HSeparator(), False, False, 0)
    self.pack_end(self.taglistview, False, False, 0)

    self.get_style_context().add_class('sidebar')
    # self.taglistview.set_valign(Gtk.Align.START)
    # btn_reveal = Gtk.Button('')
    # btn_reveal.get_style_context().add_class('btn-reveal')
    # btn_reveal.set_relief(Gtk.ReliefStyle.HALF)

    # vbox = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    # vbox.pack1(self.notebooklistview, resize=True, shrink=False)
    # vbox.pack2(self.taglistview, resize=True, shrink=False)

    # paned1 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    # paned1.pack1(self.notelistview, resize=True, shrink=False)
    # paned1.pack2(self.contentbox, resize=True, shrink=False)   
    # self.pack_end(Gtk.HSeparator(), True, False, 0)
    # self.pack_start(vbox, True, True, 0)
    # self.set_margin_left(5)
    # self.set_margin_right(5)


class BaseSidebarListView(Gtk.Box):
  
  _liststore = None
  _listiters = {}
  _trash_label = 'Trash'
  

  def __init__(self, classtype, selection_mode, header_label='', selection_all_label='', item_icon_name='', item_all_icon_name=''):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

    self._selection_mode = selection_mode
    self._classtype = classtype 
    self._header_label = header_label
    self._selection_all_label = selection_all_label
    self._item_icon_name = item_icon_name
    self._item_all_icon_name = item_all_icon_name

    # ID, Label, Icon
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

    self.selection = self._listview.get_selection()
    self.selection.set_mode(self._selection_mode)
    # self.selection.connect('changed', self._on_selection_changed)

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrollbox.add(self._listview)

    self.revealer = Gtk.Revealer()
    self.revealer.add(scrollbox)
    self.revealer.set_reveal_child(True)

    self.header = self._build_header(self._header_label)
    self.pack_start(self.header, False, False, 0)
    self.pack_start(self.revealer, True, True, 0)

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
    btn_remove = Gtk.Button.new_from_icon_name('list-remove-symbolic', Gtk.IconSize.MENU)
    btn_remove.set_relief(Gtk.ReliefStyle.NONE)
    btn_edit = Gtk.Button.new_from_icon_name('edit-symbolic', Gtk.IconSize.MENU)
    btn_edit.set_relief(Gtk.ReliefStyle.NONE)

    self.header_arrow = Gtk.Arrow()
    self.header_arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)

    eventbox = Gtk.EventBox()
    eventbox.add(self.header_arrow)
    eventbox.connect('button-press-event', self._on_arrow_pressed)

    box.pack_start(eventbox, False, False, 0)
    box.pack_start(label, False, False, 0)
    box.pack_end(btn_edit, False, False, 0)
    box.pack_end(btn_remove, False, False, 0)
    box.pack_end(btn_add, False, False, 0)

    box.set_size_request(180, 20)

    return box

  def _on_arrow_pressed(self, source, arg):
    self.revealer.set_reveal_child(not self.revealer.get_reveal_child())
    self.header_arrow.set_property('arrow-type', Gtk.ArrowType.DOWN if self.revealer.get_reveal_child() else Gtk.ArrowType.RIGHT)

  def load_all(self):
    treeiter = None
    if self._selection_mode != Gtk.SelectionMode.MULTIPLE:
      treeiter = self._liststore.append([SelectionIdConstant.NONE, self._selection_all_label, self._item_all_icon_name])
    for obj in self._classtype.select():
      self.add_obj(obj)
    if treeiter is not None:
      self._listview.get_selection().select_iter(treeiter)

  # # def _on_selection_changed(self, self.selection):
  # #   if self._selection_mode == Gtk.SelectionMode.MULTIPLE:
  # #     treepaths, model = selection.get_selected_rows()
  # #     # huh? iterate selected rows
  # #     # for treepath in treepaths:
  # #     obj_id = treepaths[0][0]
  #     self._events.emit(self._change_event_name, obj_id)

  # #   else:
  # #     model, treeiter = selection.get_selected()
  # #     if treeiter != None:
  # #       obj_id = model[treeiter][0]
  #       self._events.emit(self._change_event_name, obj_id)
  
  # Common model interface
  def add_obj(self, obj):
    self._listiters[obj.id] = self._liststore.append([obj.id, obj.get_display_name(), self._item_icon_name])
    obj.event.connect('updated', self._on_list_obj_updated)
    obj.event.connect('deleted', self._on_list_obj_deleted)

  def _on_list_obj_updated(self, event):
    obj = event.model
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.set_value(_iter, 1, obj.get_display_name())

  def _on_list_obj_deleted(self, event):
    obj = event.model
    _iter = self._listiters.get(obj.id)
    if _iter is not None:
      self._liststore.remove(_iter)

class NotebookListView(BaseSidebarListView):
  def __init__(self):
    BaseSidebarListView.__init__(
      self,
      classtype = Notebook, 
      selection_mode = Gtk.SelectionMode.BROWSE,
      header_label = 'Notebooks',
      selection_all_label = 'All Notes',
      item_icon_name = 'emblem-documents-symbolic',#'folder-documents-symbolic'
      item_all_icon_name = 'emblem-documents-symbolic')

  def load_all(self):
    BaseSidebarListView.load_all(self)
    self._liststore.append([SelectionIdConstant.TRASH, self._trash_label, 'user-trash-symbolic'])

class TagListView(BaseSidebarListView):
  def __init__(self):
    BaseSidebarListView.__init__(
      self,
      classtype = Tag, 
      selection_mode = Gtk.SelectionMode.MULTIPLE,
      header_label = 'Tags',
      item_icon_name = 'folder-tag',
      item_all_icon_name = 'folder-tag')
