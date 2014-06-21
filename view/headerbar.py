from gi.repository import Gtk
import gtkutils as GtkUtils

ALL_NOTEBOOK_ID = 'all'

class HeaderBar(Gtk.HeaderBar):

  on_after_notebook_changed = None
  _app = None

  def __init__(self, app):
    Gtk.HeaderBar.__init__(self)

    self._app = app

    #self.populate_notebooks()

    self.props.show_close_button = True
    self.set_custom_title(self._build_title_bar())

    btn_filter = GtkUtils.create_image_button('view-list-symbolic', label='Notebooks & Tags', on_click=self._on_filter_click, toggle=True)
    btn_filter.set_active(True)
    btn_addnote = GtkUtils.create_image_button('list-add-symbolic', label='New Note', on_click=None)
    # btn_find = Gtk.Button.new_from_icon_name('edit-find', Gtk.IconSize.BUTTON)
    # btn_filter.set_relief(Gtk.ReliefStyle.NONE)
    # btn_addnote.set_relief(Gtk.ReliefStyle.NONE)
    # btn_find.set_relief(Gtk.ReliefStyle.NONE)

    left_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5, valign=Gtk.Align.CENTER)
    left_box.pack_start(btn_filter, False, False, 0)
    left_box.pack_start(btn_addnote, False, False, 0)
    # left_box.pack_start(btn_find, False, False, 0)

    right_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5, valign=Gtk.Align.CENTER)
    right_box.pack_end(self._build_user_menu(), False, False, 0)

    if app.config.manual_sync:
      btn_sync = GtkUtils.create_image_button('view-refresh-symbolic', label='Sync')
      btn_sync.connect('clicked', self._on_sync_clicked)
      # btn_sync.set_relief(Gtk.ReliefStyle.NONE)
      left_box.pack_start(btn_sync, False, False, 0)

    self.pack_start(left_box)
    self.pack_end(right_box)

    self.set_status_msg(self._app.get_idle_status_msg())
  
  def set_status_msg(self, msg, in_progress=False):
    self.label_status.set_text(msg)
    self.status_spinner.set_property('active', in_progress)
    self.status_spinner.set_visible(in_progress)

  def populate_notebooks(self):
    self.combo_store = Gtk.ListStore(str, str)
    self.combo_store.append([ALL_NOTEBOOK_ID, 'All Notebooks'])
    for notebook in self._app.localstore.notebooks.values():
      self.combo_store.append([notebook.guid, notebook.name])

  def _on_sync_clicked(self, sender):
    self._app.sync()

  def _on_filter_click(self, sender):
    self._app.events.emit('sidebar_reveal', sender.get_active())

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
    label = Gtk.Label(label='louis_parengkuan')
    arrow = Gtk.Arrow(Gtk.ArrowType.DOWN)
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(image, False, False, 0)
    box.pack_start(label, False, False, 0)
    box.pack_start(arrow, False, False, 0)

    menu_btn = Gtk.MenuButton()
    menu_btn.add(box)
    menu_btn.set_relief(Gtk.ReliefStyle.NONE)
    return menu_btn




