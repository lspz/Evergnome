import os.path
import threading
import subprocess
import argparse
import socket
from gettext import gettext as _
from gi.repository import Gtk, GLib, Gdk
from util.time_util import *
from util.gtk_util import *
from view.window import AppWindow
from view.initialsetupview import InitialSetupView
from model.configs import AppConfig
from model.evernote_handler import EvernoteHandler
from model.data_models import SyncState, UserInfo
from model import db_helper, user_helper

WORKING_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
APP_CONFIG_PATH = WORKING_DIR + 'config.ini'
CSS_PATH = WORKING_DIR + 'app.css'

# huh? this starts to become more godlike, pull out functionality
class EverGnomeApp(Gtk.Application):

  def __init__(self, args):
    Gtk.Application.__init__(self)
    self.cmd_args = args

    GLib.set_application_name(_("EverGnome"))
    GLib.set_prgname('EverGnome')   
    self.connect("activate", self.on_activate)

  def on_activate(self, data=None):
    self.config = AppConfig(APP_CONFIG_PATH)
    self.db = db_helper.init_db(user_helper.get_db_path())

    devtoken = open(self.cmd_args.devtoken, 'r').read() if self.cmd_args.devtoken is not None else None 

    self.evernote_handler = EvernoteHandler(self, self.config.debug, self.config.sandbox, devtoken)
    if (devtoken is not None) or UserInfo.select().limit(1).exists():
      self.start_window()
    else :
      self._do_initial_setup()

  def start_window(self):
    self.window = AppWindow(self)
    self.window.show_all()
    self.add_window(self.window)
    self._load_css()

  def stop_window(self):
    self.remove_window(self.window)
    self.window.destroy()
    self.window = None

  def sync(self):
    worker = threading.Thread(target=self.evernote_handler.sync)
    worker.start()

  def download_resource(self, db_obj):
    worker = threading.Thread(target=self.evernote_handler.download_resource, args=[db_obj])
    worker.start()

  def open_file_external(self, path):
    if path is not None:
      # huh? Show some error msg when file is empty
      subprocess.call(["xdg-open", path])

  def get_idle_status_msg(self):
    syncstate = SyncState.get_singleton()
    if syncstate is not None:
      return 'Last sync: ' + evernote_time_to_str(syncstate.sync_time)
    else :
      return ''

  def get_current_username(self):
    return UserInfo.get_singleton().username

  def _do_initial_setup(self):
    self.setup_dlg = InitialSetupView(self)
    if self.setup_dlg.run() == Gtk.ResponseType.ACCEPT:
      self.setup_dlg.destroy()
      try:
        # self.evernote_handler.connect('oauth_dlg_opened', self._on_oauth_dlg_opened)
        self.evernote_handler.authenticate()
        self.start_window()
      except Exception as e:
        # huh? be more specifi
        print e
        show_message_dialog('Cannot connect to server. Please check your internet connection.', Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
        exit()
    else:
      exit()

  def logout(self):
    response = show_message_dialog(
      'Are you sure you want to Log Out? This will remove all saved user data.', 
      Gtk.MessageType.QUESTION, 
      Gtk.ButtonsType.YES_NO)
    if response == Gtk.ResponseType.YES:
      user_helper.archive_user_data(self.get_current_username())
      user_helper.delete_user_data(self.get_current_username())
      self.stop_window()
      self._do_initial_setup()

  def _load_css(self):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(CSS_PATH)  
    Gtk.StyleContext.add_provider_for_screen(
      Gdk.Screen.get_default(), 
      css_provider, 
      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

  @classmethod
  def create_arg_parser(cls):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--devtoken', required=False, help='File containing the devtoken')
    parser.add_argument('-rm', '--removeuserdata', action='store_true', required=False, help='Remove all user data')
    parser.add_argument('-cc', '--cleancache', action='store_true', required=False, help='Clean/Delete all unsynced objects')
    return parser









