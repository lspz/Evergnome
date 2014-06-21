from gi.repository import Gtk, Gdk, GLib
from notelistview import NoteListView
from headerbar import HeaderBar
from noteview import NoteView
from sidebarlistviews import SidebarView
from data_models import *
from consts import EvernoteProcessStatus

class SyncResultProcessor:
  add_func = None
  delete_func = None
  update_func = None

class AppWindow(Gtk.ApplicationWindow):
  
  def __init__(self, app):
    Gtk.ApplicationWindow.__init__(self, application=app)

    self.noteview = NoteView(app)
    self.contentbox = Gtk.Box()
    self.contentbox.pack_start(self.noteview, True, True, 0)

    self.headerbar = HeaderBar(app)
    self.set_titlebar(self.headerbar)

    self.sidebar = SidebarView(app)
    self.sidebar_revealer = Gtk.Revealer()
    self.sidebar_revealer.add(self.sidebar)
    self.sidebar_revealer.set_reveal_child(True)
    self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)

    self.notelistview = NoteListView(app.localstore)
    self.notelistview.load_all()

    paned1 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    paned1.pack1(self.notelistview, resize=True, shrink=False)
    paned1.pack2(self.contentbox, resize=True, shrink=False)   
    main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    main_box.pack_start(self.sidebar_revealer, False, False, 0)
    main_box.pack_start(paned1, True, True, 0)
    
    self.add(main_box)

    self._init_events()
    self._init_model_view_links()

  def _init_events(self):
    events = self.get_application().events
    events.connect('auth_started', self._on_auth_started)
    events.connect('auth_ended', self._on_auth_ended)
    events.connect('sync_started', self._on_sync_started)
    events.connect('sync_progress', self._on_sync_progress)
    events.connect('sync_ended', self._on_sync_ended)
    events.connect('notebook_changed', self.notelistview.on_notebook_changed)
    events.connect('tag_changed', self.notelistview.on_tag_changed)
    events.connect('sidebar_reveal', self._on_sidebar_reveal)

    # huh? we do this because it pass note obj, hence eliminating 1 dict lookup, not sure if worth doing
    self.notelistview.on_note_selected = self.noteview.on_note_selected

  def _init_model_view_links(self):
    # All views here must have: add_obj, update_obj, delete_obj
    # huh? should we use classname str as key instead?
    self.model_views = {}
    self.model_views[Note] = self.notelistview
    self.model_views[Notebook] = self.sidebar.notebooklistview
    self.model_views[Tag] = self.sidebar.taglistview

  # huh? wrap with GLib.idle_add?
  def _on_auth_started(self, sender):
    self.headerbar.set_status_msg('Authenticating..', in_progress=True)

  def _on_auth_ended(self, sender, result):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = self.get_application().get_idle_status_msg()
    else:
      msg = 'Authentication Failed'
    self.headerbar.set_status_msg(msg, in_progress=False)

  def _on_sidebar_reveal(self, sender, reveal):
    self.sidebar_revealer.set_reveal_child(reveal)

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
 
  def refresh_after_sync(self):
    last_sync_result = self.get_application().localstore.last_sync_result 
    if last_sync_result is None:
      return
    for obj in last_sync_result.added_list:
      self.model_views[type(obj)].add_obj(obj)
    for obj in last_sync_result.updated_list:
      self.model_views[type(obj)].update_obj(obj) # Refresh obj view
    for obj in last_sync_result.deleted_list:
      self.model_views[type(obj)].delete_obj(obj)

    # self.notelistview.refresh_filter()
    self.get_application().localstore.last_sync_result = None





