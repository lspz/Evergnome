from gi.repository import Gtk, Gdk, GLib, Gio
from notelistboxrow import NoteListBoxRow
from model.consts import SelectionIdConstant
from model.data_models import Notebook, Note

class NoteListView(Gtk.Box):

  on_note_selected = None
  _rows = {}
  _listbox = None
  _notebook_id = SelectionIdConstant.NONE
  _tag_ids = []
  # add_obj = None
  # delete_obj = None
  # update_obj = None

  def __init__(self):
    Gtk.Box.__init__(self)

    self.set_orientation(Gtk.Orientation.VERTICAL)

    self._listbox = Gtk.ListBox()
    self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    self._listbox.set_filter_func(self._filter_listbox, None)
    self._listbox.connect('row-selected', self._on_row_selected)
    self._listbox.get_style_context().add_class('note-listbox')

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrollbox.add(self._listbox)
    # scrollbox.set_size_request(400, 400)

    self.pack_start(self._create_header(), False, False, 0)
    self.pack_start(scrollbox, True, True, 0)

    self._refresh_header()

  def _create_header(self):
    self.header_label = Gtk.Label()
    self.header_label.get_style_context().add_class('sub-header-label')
    # btn_sort = Gtk.Button.new_from_icon_name('view-sort-ascending-symbolic', Gtk.IconSize.MENU)
    
    menu_sort = Gio.Menu()
    menu_sort.append('Latest', None)
    menu_sort.append('Alphabetically', None)
    box_sort = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box_sort.pack_start(Gtk.Label(label='Sort By'), False, False, 0)
    box_sort.pack_start(Gtk.Arrow(Gtk.ArrowType.DOWN), False, False, 0)
    btn_sort = Gtk.MenuButton()
    btn_sort.set_relief(Gtk.ReliefStyle.NONE)
    btn_sort.add(box_sort)
    btn_sort.set_use_popover(True)
    btn_sort.set_menu_model(menu_sort)

    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
    header_box.get_style_context().add_class('sub-header')
    header_box.pack_start(self.header_label, False, False, 0)
    header_box.pack_end(btn_sort, False, False, 0)
    return header_box

  def load_all(self):
    for note in Note.select():
      self.add_obj(note)

  # huh? this doesnt works well after sync
  def add_obj(self, note):
    row = NoteListBoxRow(note)
    self._listbox.prepend(row)  
    self._rows[note.id] = row
    note.event.connect('deleted', self._on_note_deleted)

  def _on_note_deleted(self, source):
    self.remove_row(source.model)

  # Most of the time we wouldn't go here as note is not likely to be expunged
  def remove_row(self, note):
    row = self._rows[note.id]
    self._listbox.remove(row)
    del self._rows[note.id]

  def refresh_filter(self):
    self._listbox.invalidate_filter()  

  def on_notebook_changed(self, selection):
    model, treeiter = selection.get_selected()
    if treeiter != None:
      self._notebook_id = model[treeiter][0]
      self._refresh_header()
      self._listbox.invalidate_filter()

  def on_tag_changed(self, selection):
    del self._tag_ids[:]
    selection.selected_foreach(self._add_to_tag_ids)
    self._refresh_header()
    self._listbox.invalidate_filter()    

  def _add_to_tag_ids(self, model, treepath, treeiter):
    self._tag_ids.append(model[treeiter][0])

  def _refresh_header(self):
    if self._notebook_id == SelectionIdConstant.TRASH:
      label = 'Trash'
    elif self._notebook_id == SelectionIdConstant.NONE:
      label = 'All Notes'
    else:
      notebook = Notebook.get(Notebook.id == self._notebook_id)
      label = notebook.get_display_name()
    self.header_label.set_text(label) 

  def _filter_listbox(self, listboxrow, user_data):
    note = listboxrow.note

    if self._notebook_id == SelectionIdConstant.TRASH:
      return note.is_deleted()

    return (
      (not note.is_deleted()) and
      ( (self._notebook_id == SelectionIdConstant.NONE) or (note.notebook.id == self._notebook_id) ) and 
      ( (len(self._tag_ids) == 0 ) or (note.has_tag(self._tag_ids)) )
    )

    # print 'result = ' + str(result)
    # return result

  def _on_row_selected(self, sender, listboxrow):
    if self.on_note_selected != None:
      if listboxrow != None:
        note = listboxrow.note
      else:
        note = None
      self.on_note_selected(note)




  # def update_obj(self, note):
  #   row = self._rows.get(note.id)
  #   if row is not None:
  #     row.refresh()
  #     row.changed()
  #     # huh? This doesn't work, webkit doesnt refresh and crash when selecting other note
  #     if row == self._listbox.get_selected_row():
  #       self._on_row_selected(self._listbox, row)  
