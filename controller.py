from gi.repository import Gio
import threading
from model.consts import EvernoteProcessStatus
from evernote.edam.error.ttypes import EDAMErrorCode
from util import gtk_util
from model import error_helper

class WindowController:
  def __init__(self, app, window):
    self.app = app
    self.window = window
    self.evernote_handler = self.app.evernote_handler
    self._init_events()
    self._init_actions()

  def _init_events(self):

    evernote_handler = self.evernote_handler
    window = self.window

    evernote_handler.connect('auth_started', self._on_auth_started)
    evernote_handler.connect('sync_started', self._on_sync_started)
    evernote_handler.connect('sync_progress', self._on_sync_progress)
    evernote_handler.connect('sync_ended', self._on_sync_ended)
    evernote_handler.connect('download_resource_started', self._on_download_resource_started)
    evernote_handler.connect('download_resource_ended', self._on_download_resource_ended)
    
    # huh? Cannot use signal as it crashes somehow
    evernote_handler.on_edam_error = self._on_edam_error

    window.headerbar.btn_filter.connect('toggled', self._on_toggle_sidebar)
    window.sidebar.notebooklistview.selection.connect('changed', window.notelistview.on_notebook_changed)
    window.sidebar.taglistview.selection.connect('changed',  window.notelistview.on_tag_changed)

    # huh? we do this because it pass note obj, hence eliminating 1 dict lookup, not sure if worth doing
    window.notelistview.on_note_selected = window.noteview.on_note_selected

  # To find where actions are being called, search for 'win.<action_name>'
  def _init_actions(self):
    self._create_action('new_note', self._on_new_note)
    self._create_action('sync', self._on_sync)
    self._create_action('logout', self._on_logout)

  def _create_action(self, name, on_activate):
    action = Gio.SimpleAction.new(name, None)
    action.connect('activate', on_activate)
    action.set_enabled(True)
    self.window.add_action(action)

  def _on_new_note(self, sender, extra):
    self.window.notelistview.add_new_note()

  def _on_sync(self, sender, extra):
    worker = threading.Thread(target=self.evernote_handler.sync)
    worker.start()

  # huh? pull this out of app
  def _on_logout(self, sender, extra):
    self.app.logout()

  def _on_toggle_sidebar(self, sender):
    self.window.sidebar_revealer.set_reveal_child(sender.get_active())

  def _on_sync_started(self, sender):
    self.window.headerbar.set_progress_status('Syncing..')

  def _on_sync_progress(self, sender, msg):
    self.window.headerbar.set_progress_status(msg)

  def _on_sync_ended(self, sender, result, message):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = None
      self.window.refresh_after_sync()
    else:
      msg = 'Sync Failed. ' + message
    self.window.headerbar.stop_progress_status(msg)
 
  def _on_auth_started(self, sender):
    self.window.headerbar.set_progress_status('Authenticating..')

  def _on_download_resource_started(self, sender):
    self.window.headerbar.set_progress_status('Downloading attachment..')

  def _on_download_resource_ended(self, sender, result, resource_guid, msg):
    if result == EvernoteProcessStatus.SUCCESS:
      msg = None
      resource = Resource.get(Resource.guid==resource_guid)
      if resource is not None:
        self.app.open_file_external(resource.localpath)
    else:
      msg = 'Cannot download attachment'
      if msg is not None:
        msg += '. ' + msg
    self.window.headerbar.stop_progress_status(msg)

  def _on_edam_error(self, errorcode, extra_data=''):
    if errorcode == EDAMErrorCode.AUTH_EXPIRED: 
      response = gtk_util.show_message_dialog(
        'Your authentication token has expired. Please re-authenticate again.', 
        Gtk.MessageType.QUESTION, 
        Gtk.ButtonsType.OK_CANCEL)

      # huh? THis crashes after returning from evernote
      if response == Gtk.ResponseType.OK:
        self.app.evernote_handler.perform_oauth()
