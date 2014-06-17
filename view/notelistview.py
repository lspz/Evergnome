from gi.repository import Gtk, Gdk, GLib
from notelistboxrow import NoteListBoxRow
from consts import SelectionIdConstant


class NoteListView(Gtk.Box):

  on_note_selected = None
  _localstore = None
  _rows = {}
  _listbox = None
  _notebook_id = SelectionIdConstant.NONE
  _tag_id = SelectionIdConstant.NONE
  # add_obj = None
  # delete_obj = None
  # update_obj = None

  def __init__(self, localstore):
    Gtk.Box.__init__(self)

    self._localstore = localstore

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

    self.pack_start(scrollbox, True, True, 0)

  def load_all(self):
    for note in self._localstore.notes.values():
      self.add_obj(note)

  # huh? this doesnt works well after sync
  def add_obj(self, note):
    row = NoteListBoxRow(note)
    self._listbox.prepend(row)  
    self._rows[note.id] = row

  # Most of the time we wouldn't go here as note is not likely to be expunged
  def delete_obj(self, note):
    row = self._rows[note.id]
    self._listbox.remove(row)
    del self._rows[note.id]

  def update_obj(self, note):
    row = self._rows.get(note.id)
    if row is not None:
      row.refresh()
      row.changed()
      # huh? This doesn't work, webkit doesnt refresh and crash when selecting other note
      if row == self._listbox.get_selected_row():
        self._on_row_selected(self._listbox, row)  

  def refresh_filter(self):
    self._listbox.invalidate_filter()  

  def on_notebook_changed(self, sender, notebook_id):
    self._notebook_id = notebook_id 
    self._listbox.invalidate_filter()

  def on_tag_changed(self, sender, tag_id):
    self._tag_id = tag_id 
    self._listbox.invalidate_filter()    

  def _filter_listbox(self, listboxrow, user_data):
    # print self._notebook_id
    # print self._tag_id 
    # print listboxrow.note.notebook.id
    # print listboxrow.note.is_deleted()

    note = listboxrow.note

    if self._notebook_id == SelectionIdConstant.TRASH:
      return note.is_deleted()

    return (
      (not note.is_deleted()) and
      ((self._notebook_id == SelectionIdConstant.NONE) or (note.notebook.id == self._notebook_id)) and 
      ((self._tag_id == SelectionIdConstant.NONE) or (note.has_tag(self._tag_id)) )
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



