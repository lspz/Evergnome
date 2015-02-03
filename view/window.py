from gi.repository import Gtk, Gdk, GLib, Gio
from notelistview import NoteListView
from headerbar import HeaderBar
from noteview import NoteView
from sidebarview import SidebarView
from model.data_models import *



class AppWindow(Gtk.ApplicationWindow):
  
  def __init__(self, app):
    Gtk.ApplicationWindow.__init__(self, application=app)

    self.app = app

    self.noteview = NoteView(app)

    self.headerbar = HeaderBar(app)
    self.set_titlebar(self.headerbar)

    self.sidebar = SidebarView(app)
    self.sidebar_revealer = Gtk.Revealer()
    self.sidebar_revealer.add(self.sidebar)
    self.sidebar_revealer.set_reveal_child(True)
    self.sidebar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_RIGHT)

    self.notelistview = NoteListView(app)
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

    #self._init_events()
    self._init_model_view_links()

  def _init_model_view_links(self):
    # All views here must have: add_obj
    # huh? should we use classname str as key instead?
    self.model_views = {}
    self.model_views[Note] = self.notelistview
    self.model_views[Notebook] = self.sidebar.notebooklistview
    self.model_views[Tag] = self.sidebar.taglistview


  def refresh_after_sync(self):
    last_sync_result = self.app.evernote_handler.sync_result 
    if last_sync_result is None:
      return
    for obj in last_sync_result.added_list:
      view = self.model_views.get(type(obj))
      if view is not None:
        view.add_obj(obj)
    self.app.window.notelistview.listbox.show_all()
    # self.app.window.notelistview.refresh_filter()
    self.app.evernote_handler.last_sync_result = None

  def get_selected_notebook_id(self):
    model, treeiter = self.sidebar.notebooklistview.selection.get_selected()
    if treeiter != None:
      return model[treeiter][0]
    return SelectionIdConstant.NONE

