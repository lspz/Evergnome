from gi.repository import Gtk

ALL_NOTEBOOK_ID = -1

class NotebookListView(Gtk.Box):
  def __init__(self):
    Gtk.Box(self)
    self.combo_store = Gtk.ListStore(int, str)  
    self.combo_store.append([ALL_NOTEBOOK_ID, 'All Notebooks'])

  def load(self):
    for notebook in self._app.localstore.notebooks.values():
      self.combo_store.append([notebook.id, notebook.name])