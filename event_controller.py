from gi.repository import GObject

class EventController(GObject.GObject):
  __gsignals__ = {
    'auth_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'auth_ended': (GObject.SIGNAL_RUN_FIRST, None, (int,)),

    'sync_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'sync_progress': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    'sync_ended': (GObject.SIGNAL_RUN_FIRST, None, (int,)),

    'notebook_changed': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    'tag_changed': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    'sidebar_reveal': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),

    # 'notebook_added': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    # 'notebook_deleted': (GObject.SIGNAL_RUN_FIRST, None, (str,)),

    # 'note_sel_changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    # 'note_updated': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    # 'note_added': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    # 'note_deleted': (GObject.SIGNAL_RUN_FIRST, None, (str,))

  }