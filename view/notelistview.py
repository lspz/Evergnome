import datetime
from gi.repository import Gtk, Gdk, GLib, Gio
from notelistboxrow import NoteListBoxRow
from model.consts import SelectionIdConstant
from model.data_models import Notebook, Note, ObjectStatus
from util import time_util

# Must always call show_all() on listbox everytime add new row
class NoteListView(Gtk.Box):

  on_note_selected = None
  _rows = {}
  listbox = None
  _notebook_id = SelectionIdConstant.NONE
  _tag_ids = []

  def __init__(self, app):
    Gtk.Box.__init__(self)

    self.set_orientation(Gtk.Orientation.VERTICAL)

    self.app = app

    self.listbox = Gtk.ListBox()
    self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    self.listbox.set_filter_func(self._filter_listbox, None)
    self.listbox.connect('row-selected', self._on_row_selected)
    self.listbox.get_style_context().add_class('note-listbox')

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrollbox.add(self.listbox)
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
    for note in self.app.localstore.notes.itervalues():
      self.add_obj(note)

  def add_obj(self, note):
    row = NoteListBoxRow(note)
    self.listbox.prepend(row)  
    self._rows[note.id] = row
    note.event.connect('deleted', self._on_note_deleted)
    return row

  def add_new_note(self):
    selected_notebook_id = self.app.window.get_selected_notebook_id() 
    # huh? get from localstore instead of querying
    if selected_notebook_id == SelectionIdConstant.NONE:
      notebook = self.app.evernote_handler.get_default_notebook()
    else: 
      notebook = Notebook.select().where(Notebook.id==selected_notebook_id).get() 

    now_datetime = time_util.local_datetime_to_evernote_time(datetime.datetime.now())
    new_note = Note.create(
      title = 'Untitled',
      created_time = now_datetime,
      updated_time = now_datetime,
      notebook = notebook
      )
    self.app.localstore.add_note(new_note)
    row = self.add_obj(new_note)
    self.listbox.show_all()
    self.listbox.select_row(row)

  def _on_note_deleted(self, source):
    self.remove_row(source.model)

  # Most of the time we wouldn't go here as note is not likely to be expunged
  def remove_row(self, note):
    row = self._rows[note.id]
    self.listbox.remove(row)
    del self._rows[note.id]

  def refresh_filter(self):
    self.listbox.invalidate_filter()  

  def on_notebook_changed(self, selection):
    model, treeiter = selection.get_selected()
    if treeiter != None:
      self._notebook_id = model[treeiter][0]
      self._refresh_header()
      self.refresh_filter()

  def on_tag_changed(self, selection):
    del self._tag_ids[:]
    selection.selected_foreach(self._add_to_tag_ids)
    self._refresh_header()
    self.refresh_filter()    

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

    # print note.title
    result = (
      (not note.is_deleted()) and
      ( (self._notebook_id == SelectionIdConstant.NONE) or (note.notebook.id == self._notebook_id) ) and 
      ( (len(self._tag_ids) == 0 ) or (note.has_tag(self._tag_ids)) )
    )
    if note.object_status == ObjectStatus.CREATED:
      print note.title + ' ' + str(result)
    return result

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
  #     if row == self.listbox.get_selected_row():
  #       self._on_row_selected(self.listbox, row)  
