from gi.repository import Gtk, Gdk, GLib
from notelistboxrow import NoteListBoxRow
from consts import NO_FILTER_SELECTION_ID

class NoteListView(Gtk.Box):

  on_note_selected = None
  _localstore = None
  _rows = {}
  _listbox = None
  _notebook_id = None
  _tag_id = None

  def __init__(self, localstore):
    Gtk.Box.__init__(self)

    self._localstore = localstore

    self.set_orientation(Gtk.Orientation.VERTICAL)

    self._listbox = Gtk.ListBox()
    self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    self._listbox.set_filter_func(self._filter_listbox, None)
    self._listbox.connect('row-selected', self._on_row_selected)

    self.pack_start(self._listbox, True, True, 0)

  def load_all(self):
    for note in self._localstore.notes.values():
      self.add_note(note)

  def add_note(self, note):
    row = NoteListBoxRow(note)
    self._listbox.prepend(row)  
    self._rows[note.guid] = row

  def delete_note(self, note):
    row = self._rows[note.guid]
    self._listbox.remove(row)
    del self._rows[note.guid]

  def refresh_note(self, note):
    row = self._rows.get(note.guid)
    if row is not None:
      row.refresh()
      if row == self._listbox.get_selected_row():
        self._on_row_selected(self._listbox, row)  

  def refresh_filter(self):
    self._listbox.invalidate_filter()  

  def on_notebook_changed(self, sender, notebook_id):
    self._notebook_id = notebook_id if notebook_id != NO_FILTER_SELECTION_ID else None
    self._listbox.invalidate_filter()

  def on_tag_changed(self, sender, tag_id):
    self._tag_id = tag_id if tag_id != NO_FILTER_SELECTION_ID else None
    self._listbox.invalidate_filter()    

  def _filter_listbox(self, listboxrow, user_data):
    return (
      (listboxrow.note.deleted_time is None) and 
      ((self._notebook_id == None) or (listboxrow.note.notebook.id == self._notebook_id)) and 
      ((self._tag_id == None) or (listboxrow.note.has_tag(self._tag_id)) )
    )

  def _on_row_selected(self, sender, listboxrow):
    if self.on_note_selected != None:
      if listboxrow != None:
        note = listboxrow.note
      else:
        note = None
      self.on_note_selected(note)



