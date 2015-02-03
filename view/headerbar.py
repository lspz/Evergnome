from gi.repository import Gtk, Gio
from model import user_helper
from model.data_models import UserInfo
from view.authwebview import AuthWebView # huh?
from util import gtk_util

ALL_NOTEBOOK_ID = 'all'

class HeaderBar(Gtk.HeaderBar):

  on_after_notebook_changed = None
  app = None

  def __init__(self, app):
    Gtk.HeaderBar.__init__(self)

    self.app = app

    self.props.show_close_button = True
    self.set_custom_title(self._build_title_bar())

    self.btn_filter = gtk_util.create_button(icon='view-list-symbolic', toggle=True)
    self.btn_filter.set_active(True)

    btn_new_note = gtk_util.create_button(icon='list-add-symbolic', label='New Note', action='win.new_note')

    left_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5, valign=Gtk.Align.CENTER)
    left_box.pack_start(self.btn_filter, False, False, 0)
    left_box.pack_start(btn_new_note, False, False, 0)

    right_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5, valign=Gtk.Align.CENTER)
    right_box.pack_end(self._build_user_menu(), False, False, 0)

    if app.config.manual_sync:
      btn_sync = gtk_util.create_button(icon='view-refresh-symbolic', label='Sync', action='win.sync')
      btn_sync.set_relief(Gtk.ReliefStyle.NONE)
      right_box.pack_start(btn_sync, False, False, 0)

    self.pack_start(left_box)
    self.pack_end(right_box)

    self.set_status_msg(self.app.get_idle_status_msg())

  def set_progress_status(self, msg):
    self.set_status_msg(msg, in_progress=True)

  def stop_progress_status(self, msg=None):
    self.set_status_msg(self.app.get_idle_status_msg() if msg is None else msg, in_progress=False)

  def set_status_msg(self, msg, in_progress=False):
    self.label_status.set_text(msg)
    self.status_spinner.set_property('active', in_progress)
    self.status_spinner.set_visible(in_progress)

  def _on_notebook_changed(self, combobox):
    if self.on_after_notebook_changed != None:
      active_id = combobox.get_active_id()
      active_id = active_id if active_id != ALL_NOTEBOOK_ID else None
      self.on_after_notebook_changed(active_id)

  def _build_title_bar(self):
    label_title = Gtk.Label(label='EverGnome')
    label_title.get_style_context().add_class('title')

    self.label_status = Gtk.Label(label='')
    self.label_status.get_style_context().add_class('subtitle')
    self.label_status.get_style_context().add_class('dim-label')
    self.status_spinner = Gtk.Spinner(active=False, visible=False)
    self.status_spinner.set_no_show_all(True)

    box_status = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box_status.pack_start(self.status_spinner, False, False, 0)
    box_status.pack_start(self.label_status, False, False, 0)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, expand=False, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    box.pack_start(label_title, False, False, 0)
    box.pack_start(box_status, False, False, 2)
    box.set_margin_top(5)
    box.set_margin_bottom(5)
    return box
       
  def _build_user_menu(self):
    image = Gtk.Image.new_from_icon_name('avatar-default', Gtk.IconSize.MENU)
    label = Gtk.Label(label=self.app.get_current_username())
    arrow = Gtk.Arrow(Gtk.ArrowType.DOWN)
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(image, False, False, 0)
    box.pack_start(label, False, False, 0)
    box.pack_start(arrow, False, False, 0)

    menu = Gio.Menu()
    menu.append('Log Out', 'win.logout')

    menu_btn = Gtk.MenuButton()
    menu_btn.add(box)
    menu_btn.set_menu_model(menu)
    menu_btn.set_use_popover(True)
    menu_btn.set_relief(Gtk.ReliefStyle.NONE)
    return menu_btn

