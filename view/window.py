from gi.repository import Gtk, Gdk, GLib, Gio
from notelistview import NoteListView
from headerbar import HeaderBar
from noteview import NoteView
from sidebarview import SidebarView
from model.data_models import *
from model.consts import EvernoteProcessStatus
from util import gtk_util
from model import error_helper


class AppWindow(Gtk.ApplicationWindow):
  
  def __init__(self, app):
    Gtk.ApplicationWindow.__init__(self, application=app)

    self.app = app

    self.noteview = NoteView(app)

    self.headerbar = HeaderBar(app)
    self.set_titlebar(self.headerbar)

    self.sidebar = SidebarView()
    self.sidebar_revealer = Gtk.Revealer()
    self.sidebar_revealer.add(self.sidebar)
    self.sidebar_revealer.set_reveal_child(True)
    self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)

    self.notelistview = NoteListView()
    self.notelistview.load_all()

    pane1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    pane1.pack_start(Gtk.VSeparator(), False, False, 0)
    pane1.pack_start(self.noteview, True, True, 0)
    pane2 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    pane2.pack1(self.notelistview, resize=True, shrink=False)
    pane2.pack2(pane1, resize=True, shrink=False)   
    main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    main_box.pack_start(self.sidebar_revealer, False, False, 0)
    main_box.pack_start(Gtk.VSeparator(), False, False, 0)
    main_box.pack_start(pane2, True, True, 0)
    
    self.add(main_box)

    self._init_events()
    self._init_actions()
    self._init_model_view_links()

  def _init_events(self):

    # huh? move these to app
    self.app.evernote_handler.connect('auth_started', self._on_auth_started)
    self.app.evernote_handler.connect('sync_started', self._on_sync_started)
    self.app.evernote_handler.connect('sync_progress', self._on_sync_progress)
    self.app.evernote_handler.connect('sync_ended', self._on_sync_ended)
    # self.app.evernote_handler.connect('edam_error', self._on_edam_error)

    self.app.evernote_handler.connect('download_resource_started', self._on_download_resource_started)
    self.app.evernote_handler.connect('download_resource_ended', self._on_download_resource_ended)

    self.headerbar.btn_filter.connect('toggled', self._on_sidebar_reveal)

    self.sidebar.notebooklistview.selection.connect('changed', self.notelistview.on_notebook_changed)
    self.sidebar.taglistview.selection.connect('changed',  self.notelistview.on_tag_changed)

    # huh? we do this because it pass note obj, hence eliminating 1 dict lookup, not sure if worth doing
    self.notelistview.on_note_selected = self.noteview.on_note_selected

  def _init_actions(self):
    action = Gio.SimpleAction.new('logout', None)
    action.connect('activate', self._on_logout)
    action.set_enabled(True)
    self.add_action(action)

  def _init_model_view_links(self):
    # All views here must have: add_obj
    # huh? should we use classname str as key instead?
    self.model_views = {}
    self.model_views[Note] = self.notelistview
    self.model_views[Notebook] = self.sidebar.notebooklistview
    self.model_views[Tag] = self.sidebar.taglistview

  def _on_logout(self, sender, extra):
    self.app.logout()

  def _on_sidebar_reveal(self, sender):
    self.sidebar_revealer.set_reveal_child(sender.get_active())

  def _on_sync_started(self, sender):
    self.headerbar.set_progress_msg('Syncing..')

  def _on_sync_progress(self, sender, msg):
    self.headerbar.set_progress_msg(msg)

  def _on_sync_ended(self, sender, result, message):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = None
      self.refresh_after_sync()
    else:
      msg = 'Sync Failed. ' + message
    self.headerbar.stop_progress_status(msg)
 
  def _on_auth_started(self, sender):
    self.headerbar.set_progress_msg('Authenticating..')

  def _on_download_resource_started(self, sender):
    self.headerbar.set_progress_msg('Downloading attachment..')

  def _on_download_resource_ended(self, sender, result, resource_guid):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = None
      resource = Resource.get(Resource.guid==resource_guid)
      if resource is not None:
        self.app.open_file_external(resource.localpath)
        
    else:
      msg = 'Cannot download attachment'
    self.headerbar.stop_progress_status(msg)

  # def _on_edam_error(self, sender, errorcode, extra_data):
  #   GLib.idle_add(
  #     gtk_util.show_message_dialog,
  #     error_helper.get_edam_error_msg(errorcode), Gtk.MessageType.ERROR, Gtk.ButtonsType.OK
  #     )

  def refresh_after_sync(self):
    last_sync_result = self.app.evernote_handler.last_sync_result 
    if last_sync_result is None:
      return
    for obj in last_sync_result.added_list:
      # print obj
      view = self.model_views.get(type(obj))
      # print view
      if view is not None:
        view.add_obj(obj)
    # self.notelistview.refresh_filter()
    self.app.evernote_handler.last_sync_result = None

  def get_selected_notebook_id(self):
    model, treeiter = self.sidebar.notebooklistview.selection.get_selected()
    if treeiter != None:
      return model[treeiter][0]
    return SelectionIdConstant.NONE

