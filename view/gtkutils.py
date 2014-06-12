from gi.repository import Gtk

def build_header(label):
  label = Gtk.Label(label)
  label.get_style_context().add_class('list-header-label')
  box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
  box.pack_start(label, True, True, 0)
  box.get_style_context().add_class('list-header')
  return box

def show_message_dialog(msg, message_type, buttons_type):
  flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.USE_HEADER_BAR
  dialog = Gtk.MessageDialog(self, flags, message_type, buttons_type, msg)
  response = dialog.run()
  dialog.hide()
  return response

def create_image_button(icon_name, label='', on_click=None, size=Gtk.IconSize.BUTTON, toggle=False):
  image = Gtk.Image()
  image.set_from_icon_name(icon_name, size)
  
  if toggle:
    button = Gtk.ToggleButton()
  else: 
    button = Gtk.Button()
  
  button.set_label(label)
  button.set_image(image)
  button.set_property('always_show_image', True)
  #button.set_relief(Gtk.ReliefStyle.NONE)
  if on_click != None:
    button.connect("toggled" if toggle else "clicked", on_click)

  return button
