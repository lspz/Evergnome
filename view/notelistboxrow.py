from gi.repository import Gtk, Gdk, GLib

class NoteListBoxRow(Gtk.ListBoxRow):

  def __init__(self, note):
    Gtk.ListBoxRow.__init__(self)

    note.event.connect('updated', self._on_note_updated)
    self.note = note

    self._label_title = Gtk.Label(halign=Gtk.Align.START)
    self._label_desc = Gtk.Label(halign=Gtk.Align.START)
    box_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box_left.pack_start(self._label_title, False, False, 0)
    box_left.pack_start(self._label_desc, False, False, 0)

    self._label_right = Gtk.Label(halign=Gtk.Align.END, valign=Gtk.Align.CENTER)
    box_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box_right.pack_start(self._label_right, True, True, 0)

    box = Gtk.Box(Gtk.Orientation.HORIZONTAL)
    box.set_border_width(5)
    box.pack_start(box_left, True, True, 0)
    box.pack_end(box_right, False, False, 0)

    self.get_style_context().add_class('note-listboxrow')

    self.add(box)
    
    self.refresh()

  def _on_note_updated(self, source):
    self.refresh()
    self.changed()

  def refresh(self):
    # huh? need to decode to plaintext later
    title = (self.note.title[:22] + '..') if len(self.note.title) > 24 else self.note.title
    self._label_title.set_text(title)
    self._label_title.get_style_context().add_class('note-listrow-title')
    self._label_desc.set_text(self.note.content_preview)
    self._label_desc.get_style_context().add_class('dim-label')
    self._label_right.set_text(self.note.last_updated_desc)
    self._label_right.get_style_context().add_class('note-listrow-sub')
    


