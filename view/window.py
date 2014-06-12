from gi.repository import Gtk, Gdk, GLib
from notelistview import NoteListView
from headerbar import HeaderBar
from noteview import NoteView
from sidebarlistviews import NotebookListView, TagListView
from data_models import *
from consts import EvernoteProcessStatus

class AppWindow(Gtk.ApplicationWindow):
  
  def __init__(self, app):
    Gtk.ApplicationWindow.__init__(self, application=app)

    self.noteview = NoteView(app.localstore)

    self.contentbox = Gtk.Box()
    self.contentbox.pack_start(self.noteview, True, True, 0)

    self.notelistview = NoteListView(app.localstore)
    self.notelistview.load_all()
    self.notebooklistview = NotebookListView(app)
    self.notebooklistview.load_all()
    self.taglistview = TagListView(app)
    self.taglistview.load_all()

    self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.sidebar.pack_start(self.notebooklistview, True, True, 0)
    # self.sidebar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 2)
    self.sidebar.pack_start(self.taglistview, True, True, 0)

    self.headerbar = HeaderBar(app)
    self.set_titlebar(self.headerbar)

    paned1 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    paned1.pack1(self.sidebar, resize=True, shrink=False)
    paned1.pack2(self.notelistview, resize=True, shrink=False)

    paned2 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    paned2.pack1(paned1, resize=True, shrink=False)
    paned2.pack2(self.contentbox, resize=True, shrink=False)   
    # main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    # main_box.pack_start(self.sidebar, False, False, 0)
    # main_box.pack_start(paned1, True, True, 0)
    self.add(paned2)

    self._init_events()


  def _init_events(self):
    events = self.get_application().events
    events.connect('auth_started', self._on_auth_started)
    events.connect('auth_ended', self._on_auth_ended)
    events.connect('sync_started', self._on_sync_started)
    events.connect('sync_progress', self._on_sync_progress)
    events.connect('sync_ended', self._on_sync_ended)
    events.connect('notebook_changed', self.notelistview.on_notebook_changed)
    events.connect('tag_changed', self.notelistview.on_tag_changed)

    # huh? we do this because it pass note obj, hence eliminating 1 dict lookup, not sure if worth doing
    self.notelistview.on_note_selected = self.noteview.on_note_selected

  # huh? wrap with GLib.idle_add?
  def _on_auth_started(self, sender):
    self.headerbar.set_status_msg('Authenticating..', in_progress=True)

  def _on_auth_ended(self, sender, result):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = self.get_application().get_idle_status_msg()
    else:
      msg = 'Authentication Failed'
    self.headerbar.set_status_msg(msg, in_progress=False)

  def _on_sync_started(self, sender):
    self.headerbar.set_status_msg('Syncing..', in_progress=True)

  def _on_sync_progress(self, sender, msg):
    self.headerbar.set_status_msg(msg, in_progress=True)

  def _on_sync_ended(self, sender, result):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = self.get_application().get_idle_status_msg()
      self.refresh_after_sync()
    else:
      msg = 'Sync Failed'
    self.headerbar.set_status_msg(msg, in_progress=False)

  # huh? 
  def refresh_after_sync(self):
    last_sync_result = self.get_application().localstore.last_sync_result 
    if last_sync_result is None:
      return
    for obj in last_sync_result.added_list:
      if isinstance(obj, Note):
        self.notelistview.add_note(obj)
    for obj in last_sync_result.updated_list:
      if isinstance(obj, Note):
        self.notelistview.refresh_note(obj)
    for obj in last_sync_result.deleted_list:
      if isinstance(obj, Note):
        self.notelistview.delete_note(obj)

    self.notelistview.refresh_filter()
    self.get_application().localstore.last_sync_result = None





