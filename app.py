# TODO:
# add stock
# save last value
# try mongo
# show stock detail in a revealer
# sort out how to use newer ystockquote to get company name

import os
import threading
from gettext import gettext as _
from gi.repository import Gtk, GLib, Gdk
from configs import AppConfig
from util.misc import *
from view.window import AppWindow
from event_controller import EventController
from localstore import LocalStore
from evernote_handler import EvernoteHandler

WORKING_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
APP_CONFIG_PATH = WORKING_DIR + 'config.ini'
CSS_PATH = WORKING_DIR + 'app.css'

class EverGnomeApp(Gtk.Application):

  config = None
  evernote_handler = None
  localstore = None

  def __init__(self):
    Gtk.Application.__init__(self)
    GLib.set_application_name(_("Evernote"))
    GLib.set_prgname('EverGnome')   
    self.connect("activate", self.on_activate)

  def on_activate(self, data=None):
    self.config = AppConfig(APP_CONFIG_PATH)
    self.events = EventController()
    self.localstore = LocalStore(self.config.db_path)
    self.localstore.load()
    self.evernote_handler = EvernoteHandler(self.localstore, self.events)

    self.window = AppWindow(self)
    self.window.show_all()
    self.add_window(self.window)

    self._load_css()

  def authenticate(self):
    worker = threading.Thread(target=self.evernote_handler.authenticate)
    worker.start()

  def sync(self):
    worker = threading.Thread(target=self.evernote_handler.sync)
    worker.start()

  def get_idle_status_msg(self):
    if self.localstore.syncstate is not None:
      return 'Last sync: ' + evernote_time_to_str(self.localstore.syncstate.sync_time)
    else :
      return ''

  def _load_css(self):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(CSS_PATH)  
    Gtk.StyleContext.add_provider_for_screen(
      Gdk.Screen.get_default(), 
      css_provider, 
      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)










